"""
=============================================================
  QUANTUM VACUUM ROOM — 3D Atomic Physics Simulator
=============================================================
  A pure vacuum room with zero physics by default.
  Add physics laws one by one and watch atoms respond.

  Elements supported:
    H, He, C, N, O, Fe, Ag, Au, U, Th

  Physics modules you can toggle:
    1. Gravity          — pulls atoms toward floor
    2. Thermal motion   — gives atoms kinetic energy (temperature)
    3. Electromagnetism — Coulomb repulsion between atoms
    4. Van der Waals    — weak inter-atom attraction
    5. Quantum pressure — Pauli exclusion, stops overlap
    6. Nuclear decay    — U/Th emit alpha particles over time

  Controls (keyboard):
    G  — toggle Gravity
    T  — toggle Thermal motion
    E  — toggle Electromagnetism
    V  — toggle Van der Waals
    Q  — toggle Quantum pressure
    D  — toggle Nuclear decay
    R  — Reset room (keep current physics)
    +  — increase temperature
    -  — decrease temperature
    Mouse drag — rotate view
    Scroll     — zoom

  Run:
    python quantum_vacuum_room.py
=============================================================
"""

import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.widgets import Button, CheckButtons, Slider
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import matplotlib.animation as animation
from dataclasses import dataclass, field
from typing import List, Dict
import time, sys, random

# ─────────────────────────────────────────────
#  ELEMENT DATA
# ─────────────────────────────────────────────

ELEMENTS = {
    'H':  dict(Z=1,   mass=1.008,   radius=0.53, color='#78C1FF', name='Hydrogen'),
    'He': dict(Z=2,   mass=4.003,   radius=0.31, color='#D9FFFF', name='Helium'),
    'C':  dict(Z=6,   mass=12.011,  radius=0.77, color='#444444', name='Carbon'),
    'N':  dict(Z=7,   mass=14.007,  radius=0.75, color='#3050F8', name='Nitrogen'),
    'O':  dict(Z=8,   mass=15.999,  radius=0.73, color='#FF2010', name='Oxygen'),
    'Fe': dict(Z=26,  mass=55.845,  radius=1.26, color='#E06633', name='Iron'),
    'Ag': dict(Z=47,  mass=107.868, radius=1.65, color='#C0C0C0', name='Silver'),
    'Au': dict(Z=79,  mass=196.967, radius=1.74, color='#FFD700', name='Gold'),
    'U':  dict(Z=92,  mass=238.029, radius=1.96, color='#008FFF', name='Uranium',  radioactive=True),
    'Th': dict(Z=90,  mass=232.038, radius=1.79, color='#00BAFF', name='Thorium',  radioactive=True),
}

# ─────────────────────────────────────────────
#  ATOM
# ─────────────────────────────────────────────

@dataclass
class Atom:
    symbol: str
    pos: np.ndarray        # [x, y, z]  Angstroms
    vel: np.ndarray        # [vx,vy,vz] Å/fs
    acc: np.ndarray = field(default_factory=lambda: np.zeros(3))
    alpha_emitted: int = 0
    age: float = 0.0       # femtoseconds

    @property
    def Z(self):   return ELEMENTS[self.symbol]['Z']
    @property
    def mass(self): return ELEMENTS[self.symbol]['mass']
    @property
    def radius(self): return ELEMENTS[self.symbol]['radius']
    @property
    def color(self): return ELEMENTS[self.symbol]['color']
    @property
    def is_radioactive(self): return ELEMENTS[self.symbol].get('radioactive', False)


# ─────────────────────────────────────────────
#  PHYSICS ENGINE
# ─────────────────────────────────────────────

class PhysicsEngine:
    def __init__(self):
        self.gravity        = False
        self.thermal        = False
        self.em             = False
        self.vdw            = False
        self.quantum_press  = False
        self.decay          = False

        self.temperature    = 300.0   # Kelvin
        self.g_strength     = 9.8e-4  # Å/fs² (scaled)
        self.dt             = 0.5     # femtoseconds

        self.k_B  = 8.617e-5   # eV/K
        self.k_e  = 14.4       # eV·Å  (Coulomb constant in atomic units)

        self.decay_events: List[dict] = []

    def compute_forces(self, atoms: List[Atom], box: np.ndarray) -> None:
        """Zero all accelerations then accumulate physics."""
        for a in atoms:
            a.acc = np.zeros(3)

        # 1. GRAVITY
        if self.gravity:
            for a in atoms:
                a.acc[2] -= self.g_strength   # -z = floor

        # 2. ELECTROMAGNETISM (Coulomb)
        if self.em:
            n = len(atoms)
            for i in range(n):
                for j in range(i+1, n):
                    r_vec = atoms[i].pos - atoms[j].pos
                    dist  = np.linalg.norm(r_vec)
                    if dist < 0.3:
                        dist = 0.3
                    # F = k * Z_i * Z_j / r²  (repulsive — same sign charges simplified)
                    force_mag = self.k_e * atoms[i].Z * atoms[j].Z / (dist**2) * 0.001
                    force = force_mag * (r_vec / dist)
                    atoms[i].acc += force / atoms[i].mass
                    atoms[j].acc -= force / atoms[j].mass

        # 3. VAN DER WAALS (Lennard-Jones 6-12 simplified)
        if self.vdw:
            n = len(atoms)
            for i in range(n):
                for j in range(i+1, n):
                    r_vec = atoms[i].pos - atoms[j].pos
                    dist  = np.linalg.norm(r_vec)
                    sigma = (atoms[i].radius + atoms[j].radius) * 0.8
                    if dist < 0.2: dist = 0.2
                    sr6  = (sigma/dist)**6
                    sr12 = sr6**2
                    # LJ force magnitude
                    force_mag = 24 * 0.01 * (2*sr12 - sr6) / dist
                    force = force_mag * (r_vec / dist)
                    atoms[i].acc += force / atoms[i].mass
                    atoms[j].acc -= force / atoms[j].mass

        # 4. QUANTUM PRESSURE (hard-core repulsion / Pauli exclusion)
        if self.quantum_press:
            n = len(atoms)
            for i in range(n):
                for j in range(i+1, n):
                    r_vec = atoms[i].pos - atoms[j].pos
                    dist  = np.linalg.norm(r_vec)
                    min_d = (atoms[i].radius + atoms[j].radius) * 0.5
                    if dist < min_d:
                        overlap = min_d - dist
                        force = 50.0 * overlap * (r_vec / (dist+1e-9))
                        atoms[i].acc += force / atoms[i].mass
                        atoms[j].acc -= force / atoms[j].mass

    def integrate(self, atoms: List[Atom], box: np.ndarray) -> None:
        """Velocity Verlet integration + wall bounce."""
        for a in atoms:
            a.vel += 0.5 * a.acc * self.dt
            a.pos += a.vel * self.dt

            # Wall collisions (elastic bounce)
            for d in range(3):
                lo, hi = 0.0, box[d]
                if a.pos[d] < lo:
                    a.pos[d] = lo
                    a.vel[d] = abs(a.vel[d]) * 0.85
                elif a.pos[d] > hi:
                    a.pos[d] = hi
                    a.vel[d] = -abs(a.vel[d]) * 0.85

            a.age += self.dt

        # Recompute forces after move
        self.compute_forces(atoms, box)

        for a in atoms:
            a.vel += 0.5 * a.acc * self.dt

    def apply_thermostat(self, atoms: List[Atom]) -> None:
        """Andersen thermostat — random velocity kicks toward target T."""
        if not self.thermal or not atoms:
            return
        sigma = np.sqrt(self.k_B * self.temperature)   # speed scale (eV-based, scaled)
        for a in atoms:
            if random.random() < 0.02:   # 2% chance per step per atom
                speed = sigma / np.sqrt(a.mass) * 15.0
                a.vel = np.random.normal(0, speed, 3)

    def try_decay(self, atoms: List[Atom]) -> List[Atom]:
        """Nuclear decay for U/Th — emit He-4 (alpha) occasionally."""
        if not self.decay:
            return []
        new_atoms = []
        for a in atoms:
            if a.is_radioactive:
                # Probability per step (very accelerated for visualization)
                prob = 1e-4 if a.symbol == 'U' else 5e-5
                if random.random() < prob:
                    # Emit alpha (He-4) in random direction
                    direction = np.random.normal(0, 1, 3)
                    direction /= np.linalg.norm(direction)
                    alpha_speed = 0.5
                    alpha = Atom(
                        symbol='He',
                        pos=a.pos.copy() + direction * (a.radius + 0.5),
                        vel=direction * alpha_speed
                    )
                    new_atoms.append(alpha)
                    # Daughter nucleus recoils
                    a.vel -= direction * alpha_speed * 4 / a.mass
                    a.alpha_emitted += 1
                    self.decay_events.append({
                        'symbol': a.symbol,
                        'time': a.age,
                        'pos': a.pos.copy()
                    })
        return new_atoms


# ─────────────────────────────────────────────
#  ROOM (simulation state)
# ─────────────────────────────────────────────

class VacuumRoom:
    def __init__(self, size=20.0):
        self.size   = size
        self.box    = np.array([size, size, size])
        self.atoms: List[Atom] = []
        self.engine = PhysicsEngine()
        self.step   = 0
        self.log: List[str] = ["[VACUUM ROOM INITIALIZED — zero physics]",
                                "[Pure empty space. No forces. No energy.]"]

    def add_atom(self, symbol: str, pos=None, vel=None):
        if symbol not in ELEMENTS:
            self.log.append(f"[Unknown element: {symbol}]")
            return
        if pos is None:
            pos = np.random.uniform(2, self.size-2, 3)
        if vel is None:
            vel = np.zeros(3)
        self.atoms.append(Atom(symbol=symbol, pos=np.array(pos, float),
                               vel=np.array(vel, float)))
        self.log.append(f"[Added {ELEMENTS[symbol]['name']} ({symbol}) at {pos.round(1)}]")

    def add_preset(self, name: str):
        """Named atom configurations."""
        configs = {
            'noble gases':  [('He',3),('He',3)],
            'organic':      [('C',2),('H',4),('N',1),('O',2)],
            'metals':       [('Fe',2),('Au',1),('Ag',2)],
            'radioactive':  [('U',2),('Th',2)],
            'all elements': [(s,1) for s in ELEMENTS],
        }
        if name not in configs:
            return
        for sym, count in configs[name]:
            for _ in range(count):
                self.add_atom(sym)

    def reset_atoms(self):
        self.atoms = []
        self.engine.decay_events = []
        self.step = 0
        self.log.append("[Room cleared — vacuum restored]")

    def tick(self):
        """One simulation step."""
        eng = self.engine
        eng.compute_forces(self.atoms, self.box)
        eng.integrate(self.atoms, self.box)
        eng.apply_thermostat(self.atoms)
        new = eng.try_decay(self.atoms)
        self.atoms.extend(new)
        self.step += 1


# ─────────────────────────────────────────────
#  VISUALIZER
# ─────────────────────────────────────────────

class RoomVisualizer:
    def __init__(self, room: VacuumRoom):
        self.room = room
        self._build_ui()
        self._anim_running = True
        self._rotation = [30, 45]   # elev, azim

    def _build_ui(self):
        self.fig = plt.figure(figsize=(15, 9), facecolor='#0d0d0d')
        self.fig.suptitle('QUANTUM VACUUM ROOM', color='#aaaaaa',
                           fontsize=13, fontfamily='monospace', y=0.98)

        # ── 3D viewport ──────────────────────────────
        self.ax3d = self.fig.add_axes([0.02, 0.08, 0.62, 0.88], projection='3d')
        self._style_3d()

        # ── Right panel ──────────────────────────────
        # Physics toggles
        self.ax_chk = self.fig.add_axes([0.67, 0.60, 0.30, 0.34])
        self.ax_chk.set_facecolor('#111111')
        self.ax_chk.set_title('PHYSICS MODULES', color='#888888',
                               fontsize=9, fontfamily='monospace', pad=4)
        labels = ['Gravity', 'Thermal motion', 'Electromagnetism',
                  'Van der Waals', 'Quantum pressure', 'Nuclear decay']
        self.chk = CheckButtons(self.ax_chk, labels,
                                [False]*6)
        self.chk.on_clicked(self._toggle_physics)
        for txt in self.chk.labels:
            txt.set_fontfamily('monospace')
            txt.set_fontsize(9)
            txt.set_color('#cccccc')

        # Temperature slider
        self.ax_temp = self.fig.add_axes([0.67, 0.52, 0.30, 0.04])
        self.sl_temp = Slider(self.ax_temp, 'Temp (K)', 1, 5000,
                              valinit=300, color='#334455')
        self.sl_temp.label.set_color('#aaaaaa')
        self.sl_temp.label.set_fontfamily('monospace')
        self.sl_temp.label.set_fontsize(8)
        self.sl_temp.valtext.set_color('#aaaaaa')
        self.sl_temp.on_changed(self._set_temp)

        # Add-atom buttons
        self.ax_btns = self.fig.add_axes([0.67, 0.36, 0.30, 0.14])
        self.ax_btns.set_facecolor('#111111')
        self.ax_btns.axis('off')
        self.ax_btns.set_title('ADD ATOMS', color='#888888',
                               fontsize=9, fontfamily='monospace', pad=4)

        btn_specs = [
            ('H',  [0.67, 0.295, 0.047, 0.038]),
            ('He', [0.72, 0.295, 0.047, 0.038]),
            ('C',  [0.77, 0.295, 0.047, 0.038]),
            ('N',  [0.82, 0.295, 0.047, 0.038]),
            ('O',  [0.87, 0.295, 0.047, 0.038]),
            ('Fe', [0.92, 0.295, 0.047, 0.038]),
            ('Ag', [0.67, 0.250, 0.047, 0.038]),
            ('Au', [0.72, 0.250, 0.047, 0.038]),
            ('U',  [0.77, 0.250, 0.047, 0.038]),
            ('Th', [0.82, 0.250, 0.047, 0.038]),
        ]
        self._atom_btns = []
        for sym, rect in btn_specs:
            ax = self.fig.add_axes(rect)
            c  = ELEMENTS[sym]['color']
            b  = Button(ax, sym, color='#1a1a1a', hovercolor='#2a2a2a')
            b.label.set_color(c)
            b.label.set_fontfamily('monospace')
            b.label.set_fontsize(9)
            b.label.set_fontweight('bold')
            b.on_clicked(lambda ev, s=sym: self._add_atom_btn(s))
            self._atom_btns.append(b)

        # Preset buttons
        presets = [
            ('Noble gases',  [0.67, 0.205, 0.095, 0.038]),
            ('Organic',      [0.77, 0.205, 0.095, 0.038]),
            ('Metals',       [0.87, 0.205, 0.095, 0.038]),
            ('Radioactive',  [0.67, 0.162, 0.095, 0.038]),
            ('All elements', [0.77, 0.162, 0.115, 0.038]),
        ]
        self._preset_btns = []
        for label, rect in presets:
            ax = self.fig.add_axes(rect)
            b  = Button(ax, label, color='#1a1a2a', hovercolor='#2a2a3a')
            b.label.set_color('#8899cc')
            b.label.set_fontfamily('monospace')
            b.label.set_fontsize(7.5)
            key = label.lower()
            b.on_clicked(lambda ev, k=key: self._add_preset_btn(k))
            self._preset_btns.append(b)

        # Reset / Pause buttons
        ax_reset = self.fig.add_axes([0.67, 0.108, 0.14, 0.038])
        self.btn_reset = Button(ax_reset, 'RESET ROOM',
                                color='#2a1111', hovercolor='#3a1111')
        self.btn_reset.label.set_color('#ff6644')
        self.btn_reset.label.set_fontfamily('monospace')
        self.btn_reset.label.set_fontsize(8)
        self.btn_reset.on_clicked(self._reset)

        ax_pause = self.fig.add_axes([0.83, 0.108, 0.14, 0.038])
        self.btn_pause = Button(ax_pause, 'PAUSE',
                                color='#112211', hovercolor='#223322')
        self.btn_pause.label.set_color('#66ff88')
        self.btn_pause.label.set_fontfamily('monospace')
        self.btn_pause.label.set_fontsize(8)
        self.btn_pause.on_clicked(self._toggle_pause)

        # Log panel
        self.ax_log = self.fig.add_axes([0.67, 0.01, 0.30, 0.09])
        self.ax_log.set_facecolor('#0a0a0a')
        self.ax_log.axis('off')
        self.ax_log.set_title('SYSTEM LOG', color='#555555',
                               fontsize=8, fontfamily='monospace', pad=2)
        self._log_txt = self.ax_log.text(0.01, 0.85, '', transform=self.ax_log.transAxes,
                                          color='#44aa66', fontsize=7,
                                          fontfamily='monospace', va='top')

        # Status bar
        self.ax_status = self.fig.add_axes([0.02, 0.01, 0.62, 0.04])
        self.ax_status.set_facecolor('#0a0a0a')
        self.ax_status.axis('off')
        self._status_txt = self.ax_status.text(0.01, 0.5, '',
                                               transform=self.ax_status.transAxes,
                                               color='#666688', fontsize=8,
                                               fontfamily='monospace', va='center')

    def _style_3d(self):
        ax = self.ax3d
        s  = self.room.size
        ax.set_facecolor('#050508')
        ax.set_xlim(0, s); ax.set_ylim(0, s); ax.set_zlim(0, s)
        ax.set_xlabel('X (Å)', color='#334455', fontsize=7)
        ax.set_ylabel('Y (Å)', color='#334455', fontsize=7)
        ax.set_zlabel('Z (Å)', color='#334455', fontsize=7)
        ax.tick_params(colors='#223344', labelsize=6)
        for pane in [ax.xaxis.pane, ax.yaxis.pane, ax.zaxis.pane]:
            pane.fill = False
            pane.set_edgecolor('#111122')
        ax.grid(True, color='#111122', linewidth=0.3, alpha=0.5)
        # Draw room wireframe
        verts = [
            [[0,0,0],[s,0,0],[s,s,0],[0,s,0]],  # floor
            [[0,0,s],[s,0,s],[s,s,s],[0,s,s]],  # ceiling
        ]
        floor = Poly3DCollection([[[0,0,0],[s,0,0],[s,s,0],[0,s,0]]],
                                  alpha=0.04, facecolor='#334466',
                                  edgecolor='#223355', linewidth=0.5)
        ax.add_collection3d(floor)
        # Edges
        edges = [
            ([0,s],[0,0],[0,0]),([0,s],[s,s],[0,0]),
            ([0,0],[0,s],[0,0]),([0,0],[0,0],[0,s]),
            ([s,s],[0,s],[0,0]),([s,s],[0,0],[0,s]),
            ([0,s],[0,0],[s,s]),([0,s],[s,s],[s,s]),
            ([0,0],[0,s],[s,s]),([s,s],[0,s],[s,s]),
        ]
        for xe,ye,ze in edges:
            ax.plot(xe,ye,ze, color='#223355', lw=0.4, alpha=0.5)

    # ── callbacks ─────────────────────────────

    def _toggle_physics(self, label):
        eng = self.room.engine
        map_ = {
            'Gravity':         'gravity',
            'Thermal motion':  'thermal',
            'Electromagnetism':'em',
            'Van der Waals':   'vdw',
            'Quantum pressure':'quantum_press',
            'Nuclear decay':   'decay',
        }
        attr = map_.get(label)
        if attr:
            setattr(eng, attr, not getattr(eng, attr))
            state = 'ON' if getattr(eng, attr) else 'OFF'
            self.room.log.append(f"[{label}: {state}]")

    def _set_temp(self, val):
        self.room.engine.temperature = val

    def _add_atom_btn(self, sym):
        self.room.add_atom(sym)

    def _add_preset_btn(self, key):
        self.room.add_preset(key)

    def _reset(self, ev):
        self.room.reset_atoms()

    def _toggle_pause(self, ev):
        self._anim_running = not self._anim_running
        self.btn_pause.label.set_text('RESUME' if not self._anim_running else 'PAUSE')

    # ── animation frame ───────────────────────

    def _frame(self, _):
        if self._anim_running:
            for _ in range(4):   # sub-steps per frame
                self.room.tick()

        self.ax3d.cla()
        self._style_3d()
        self.ax3d.view_init(elev=25, azim=(self.room.step * 0.15) % 360)

        # Draw atoms
        atoms = self.room.atoms
        if atoms:
            xs = [a.pos[0] for a in atoms]
            ys = [a.pos[1] for a in atoms]
            zs = [a.pos[2] for a in atoms]
            cs = [a.color  for a in atoms]
            ss = [max(20, min(300, a.radius * 60)) for a in atoms]

            self.ax3d.scatter(xs, ys, zs, c=cs, s=ss,
                              alpha=0.92, edgecolors='white',
                              linewidths=0.3, depthshade=True)

            # Labels
            for a in atoms:
                self.ax3d.text(a.pos[0], a.pos[1], a.pos[2]+0.8,
                               a.symbol, fontsize=6, color=a.color,
                               ha='center', fontfamily='monospace')

            # Velocity vectors (if thermal)
            if self.room.engine.thermal:
                for a in atoms:
                    speed = np.linalg.norm(a.vel)
                    if speed > 0.01:
                        v_norm = a.vel / (speed + 1e-9) * min(speed * 3, 3.0)
                        self.ax3d.quiver(a.pos[0], a.pos[1], a.pos[2],
                                         v_norm[0], v_norm[1], v_norm[2],
                                         color='#ffaa44', alpha=0.5,
                                         length=1.0, normalize=False,
                                         arrow_length_ratio=0.3, linewidth=0.6)

        # Physics state title
        eng = self.room.engine
        active = []
        if eng.gravity:       active.append('GRAVITY')
        if eng.thermal:       active.append(f'THERMAL({eng.temperature:.0f}K)')
        if eng.em:            active.append('EM')
        if eng.vdw:           active.append('VdW')
        if eng.quantum_press: active.append('PAULI')
        if eng.decay:         active.append('DECAY')

        phys_str = '  '.join(active) if active else 'PURE VACUUM — no physics'
        self.ax3d.set_title(phys_str, color='#4488aa',
                            fontsize=8, fontfamily='monospace', pad=6)

        # Status bar
        ke = sum(0.5 * a.mass * np.dot(a.vel, a.vel) for a in atoms) if atoms else 0
        decays = len(self.room.engine.decay_events)
        self._status_txt.set_text(
            f"atoms: {len(atoms):3d}  |  step: {self.room.step:6d}  |  "
            f"KE: {ke:.3f} eV  |  decays: {decays}"
        )

        # Log
        log_lines = self.room.log[-5:]
        self._log_txt.set_text('\n'.join(log_lines))

        return []

    def run(self):
        self.anim = animation.FuncAnimation(
            self.fig, self._frame, interval=40,
            blit=False, cache_frame_data=False
        )
        plt.show()


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────

def main():
    print(__doc__)
    print("Starting Quantum Vacuum Room...")
    print("Close the window to exit.\n")

    room = VacuumRoom(size=20.0)

    # Start with a few atoms so there's something to see
    room.add_atom('C',  pos=np.array([5.0, 5.0, 10.0]))
    room.add_atom('O',  pos=np.array([10.0, 10.0, 10.0]))
    room.add_atom('H',  pos=np.array([7.0, 7.0, 12.0]))
    room.add_atom('Fe', pos=np.array([14.0, 8.0, 10.0]))
    room.add_atom('Au', pos=np.array([8.0, 14.0, 10.0]))

    viz = RoomVisualizer(room)
    viz.run()

if __name__ == '__main__':
    main()