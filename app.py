import math
import random
import os
from dataclasses import dataclass

import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

st.set_page_config(page_title="Eye-Black-Hole Universe Simulator", layout="wide")

st.title("Eye-Black-Hole Universe Simulator")
st.caption("A playful Streamlit thought experiment blending vision, gravity, quantum observation, and philosophy.")

with st.sidebar:
    st.header("Universe controls")
    mode = st.selectbox(
        "Sight mechanism",
        ["Passive eye (our universe)", "Gravitational eye", "Conscious observer field"],
        index=1,
    )
    n_rays = st.slider("Photons / rays", 100, 3000, 900, 100)
    slit_gap = st.slider("Slit gap", 0.4, 3.0, 1.2, 0.1)
    eye_mass_factor = st.slider("Eye gravity factor", 0.0, 5.0, 1.8, 0.1)
    consciousness = st.slider("Consciousness weight", 0, 100, 50, 5)
    observer_on = st.toggle("Observer active", value=True)
    creativity = st.slider("GenAI creativity", 0.0, 1.0, 0.6, 0.05)

@dataclass
class SimResult:
    df: pd.DataFrame
    hits_left: int
    hits_right: int
    hits_center: int
    curvature: float


def simulate(n, slit_gap, gravity, observer, consciousness, mode):
    rng = np.random.default_rng(42)
    x = np.linspace(0, 10, n)
    y0 = rng.normal(0, 1.2, n)
    slit_choice = rng.choice([-1, 1], size=n)
    slit_y = slit_choice * slit_gap

    if mode == "Passive eye (our universe)":
        phase = rng.uniform(0, 2 * np.pi, n)
        y = 0.6 * np.sin(4 * x + phase) + 0.35 * np.sin(9 * x + phase / 2)
        curvature = 0.05
    elif mode == "Gravitational eye":
        pull = gravity * (2.2 / (1 + (x - 7.8) ** 2))
        y = y0 * (1 - np.clip(pull / 4, 0, 0.95)) + slit_y * 0.25
        y -= np.sign(y) * pull * 0.35
        curvature = float(np.mean(pull))
    else:
        collapse = (consciousness / 100.0) * (1.0 if observer else 0.35)
        noise = rng.normal(0, 0.22 + (1 - collapse) * 0.6, n)
        y = slit_y * collapse + noise
        curvature = collapse

    if observer:
        collapse = consciousness / 100.0
        y = y * (1 - 0.55 * collapse) + rng.normal(0, 0.08 + 0.18 * (1 - collapse), n)

    x_screen = np.full(n, 10.0)
    bins = pd.cut(y, bins=[-10, -0.75, 0.75, 10], labels=["left", "center", "right"])
    hits_left = int((bins == "left").sum())
    hits_center = int((bins == "center").sum())
    hits_right = int((bins == "right").sum())

    df = pd.DataFrame({"x": x_screen, "y": y, "region": bins.astype(str)})
    return SimResult(df, hits_left, hits_right, hits_center, curvature)


result = simulate(n_rays, slit_gap, eye_mass_factor, observer_on, consciousness, mode)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Rays fired", n_rays)
c2.metric("Left hits", result.hits_left)
c3.metric("Center hits", result.hits_center)
c4.metric("Right hits", result.hits_right)

fig = go.Figure()
fig.add_vline(x=3.0, line_width=4, line_color="gray", opacity=0.6)
fig.add_vline(x=7.8, line_width=4, line_color="gray", opacity=0.35)
fig.add_annotation(x=3.0, y=2.6, text="Slits / threshold", showarrow=False, font=dict(color="gray"))
fig.add_annotation(x=7.8, y=2.6, text="Eye / horizon", showarrow=False, font=dict(color="gray"))
colors = {"left": "#7c83fd", "center": "#10b981", "right": "#f97316"}
for region in ["left", "center", "right"]:
    sub = result.df[result.df["region"] == region]
    fig.add_trace(go.Scatter(
        x=sub["x"], y=sub["y"], mode="markers",
        marker=dict(size=6, color=colors[region], opacity=0.65),
        name=f"{region} hits"
    ))
fig.update_layout(
    height=520,
    template="plotly_dark",
    paper_bgcolor="#0b1020",
    plot_bgcolor="#0b1020",
    margin=dict(l=10, r=10, t=40, b=10),
    xaxis=dict(title="Universe axis", range=[0, 10.8], showgrid=True, gridcolor="rgba(255,255,255,0.06)"),
    yaxis=dict(title="Deflection / perception", range=[-3, 3], showgrid=True, gridcolor="rgba(255,255,255,0.06)"),
    legend=dict(orientation="h", y=1.02, x=0)
)
st.plotly_chart(fig, use_container_width=True)

st.subheader("Interpretation")
if mode == "Passive eye (our universe)":
    interp = "This mode treats vision as reception. Light arrives, the eye records it, and the world mostly remains independent of the observer."
elif mode == "Gravitational eye":
    interp = "This mode imagines the eye as an active attractor. The stronger the eye gravity factor, the more visual rays bend inward as if perception literally pulls the world toward the observer."
else:
    interp = "This mode models observation as a reality-shaping field. Higher consciousness weight pushes the system from ambiguity toward collapse."
st.write(interp)
st.write(f"Current curvature / collapse index: **{result.curvature:.3f}**")

st.subheader("GenAI reflection")
user_prompt = st.text_area(
    "Ask the in-app philosopher",
    value="If eyes pulled light like black holes, would seeing become a form of touching reality?",
    height=100,
)

def faux_genai(prompt, mode, observer, consciousness, creativity):
    angle = "metaphysical" if creativity > 0.66 else "analytical" if creativity < 0.33 else "balanced"
    obs = "active" if observer else "inactive"
    if mode == "Gravitational eye":
        thesis = "Perception becomes an intervention, not a snapshot"
        body = "In this universe, sight would no longer be passive registration. To see something would be to bend its path toward you, making attention a physical force."
    elif mode == "Conscious observer field":
        thesis = "Observation becomes part of ontology"
        body = "Reality would not simply wait to be measured. It would stabilize in response to observation, with consciousness acting less like a witness and more like a participant."
    else:
        thesis = "Perception remains representational"
        body = "The eye receives rather than summons. That keeps a useful distance between the world and the model your brain builds from incoming signals."
    flourish = {
        "metaphysical": "The unsettling implication is that privacy, objectivity, and distance all become fragile once attention itself has gravity.",
        "balanced": "Philosophically, that blurs the line between epistemology, how you know, and ontology, what exists.",
        "analytical": "From a modeling perspective, the observer changes boundary conditions rather than merely reading outputs."
    }[angle]
    return f"**Thesis:** {thesis}.\n\n**Response to your prompt:** {prompt}\n\n{body} The observer is currently **{obs}**, with consciousness weight at **{consciousness}%**. {flourish}"

st.markdown(faux_genai(user_prompt, mode, observer_on, consciousness, creativity))

st.subheader("How to run locally")
st.code("pip install streamlit plotly numpy pandas\nstreamlit run app.py", language="bash")
