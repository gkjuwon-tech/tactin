"""TACTIN — vibe hardware for the engineer's workbench.

An AI agent that controls a desktop robot arm to assemble electronic
components on a prototyping bench. The developer drops parts on the bench
and describes the build in natural language; vision localizes the parts,
an LLM plans the pick-and-place sequence, and the arm does the work.

The core (geometry, kinematics, safety, workspace) is pure-Python and has
no third-party dependencies, so it runs and tests anywhere. Hardware and
LLM integrations (pyserial, opencv, anthropic) are optional extras that are
imported lazily — the system falls back to simulation when they are absent.
"""

__version__ = "0.1.0"

from .config import ArmSpec, Config
from .geometry import Pose
from .kinematics import JointState, UnreachableError, forward_kinematics, inverse_kinematics

__all__ = [
    "ArmSpec",
    "Config",
    "Pose",
    "JointState",
    "UnreachableError",
    "forward_kinematics",
    "inverse_kinematics",
]
