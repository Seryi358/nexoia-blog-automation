"""Featured image prompt templates for KIE AI Nano Banana 2.

Rotates through 4 visual treatments so featured images don't all look the same.
All variants keep the IA Practica brand palette.
"""

BRAND_PALETTE = "deep blue #1E40AF, violet #7C3AED, cyan #06B6D4, light blue-white #F0F4FF background"

STYLE_VARIANTS = {
    "flat_illustration": (
        "Modern flat vector illustration with clean geometric shapes, subtle gradients, "
        "minimalist composition. Professional tech editorial look reminiscent of Stripe "
        "or Notion blog headers. Single focal object or metaphor centered-left with "
        "breathing space on the right."
    ),
    "isometric_3d": (
        "Isometric 3D illustration style (like Dribbble editorial pieces) with clean "
        "geometric props, soft shadows, floating UI cards and connection lines. High "
        "detail but still minimalistic, single hero scene centered."
    ),
    "abstract_gradient": (
        "Abstract gradient composition with soft blurred shapes, glass-morphism cards "
        "overlaid, subtle grain texture. Modern editorial style used by AI-first "
        "publications (Stripe Press, Every, Not Boring). No characters, just shapes."
    ),
    "editorial_collage": (
        "Editorial magazine collage style with layered geometric shapes, dotted "
        "patterns, subtle paper texture, one bold accent shape. Think New York Times "
        "or Vox tech-feature illustration."
    ),
}

FEATURED_IMAGE_PROMPT = """Create a professional blog featured image for an article titled: "{topic}"

STYLE: {style_description}

COLOR PALETTE: {palette}. Keep high contrast between elements and background so the image still reads at 16:9 thumbnail size.

VISUAL ELEMENTS: {visual_elements}. Balance the composition - do not clutter.

MOOD: Professional, innovative, optimistic. LatAm business-blog aesthetic, not Silicon Valley cliche.

HARD CONSTRAINTS:
- Absolutely NO text, letters, numbers, or symbols in the image
- NO photorealistic faces or humans (illustrated abstract silhouettes allowed)
- NO generic stock-photo shots of laptops or people at desks
- NO watermarks or logos
- High resolution suitable for 2K export, 16:9 landscape orientation
- Clean, intentional composition with clear focal point
"""


def build_image_prompt(topic: str, visual_elements: str, style_key: str = "flat_illustration") -> str:
    """Render the image prompt for a given archetype. Caller picks the style key to rotate them."""
    style = STYLE_VARIANTS.get(style_key, STYLE_VARIANTS["flat_illustration"])
    return FEATURED_IMAGE_PROMPT.format(
        topic=topic,
        visual_elements=visual_elements,
        style_description=style,
        palette=BRAND_PALETTE,
    )
