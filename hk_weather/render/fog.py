"""Screen-space depth fog shared by the desktop scene actors."""

from hk_weather.core.config import (
    BACKGROUND_COLOUR,
    DEPTH_FOG_END,
    DEPTH_FOG_START,
    DEPTH_FOG_STRENGTH,
)


def _rgb(colour):
    value = colour.lstrip("#")
    return tuple(int(value[index : index + 2], 16) / 255.0 for index in (0, 2, 4))


def add_depth_fog(actor):
    """Blend fragments into the background using their screen-space depth."""
    red, green, blue = _rgb(BACKGROUND_COLOUR)
    replacement = f"""
//VTK::Light::Impl
float weatherFog = smoothstep({DEPTH_FOG_START:.6f}, {DEPTH_FOG_END:.6f}, gl_FragCoord.z);
weatherFog = clamp(weatherFog * {DEPTH_FOG_STRENGTH:.6f}, 0.0, 1.0);
gl_FragData[0].rgb = mix(gl_FragData[0].rgb, vec3({red:.6f}, {green:.6f}, {blue:.6f}), weatherFog);
"""
    actor.GetShaderProperty().AddFragmentShaderReplacement(
        "//VTK::Light::Impl",
        True,
        replacement,
        False,
    )
    return actor
