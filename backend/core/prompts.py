"""Prompt templates for AI image generation."""


def get_empty_room_prompt():
    """Generate prompt for removing all furniture from a room."""
    return (
        "Remove all furniture, people, and objects from this room. "
        "Show the room completely empty with bare walls and flooring. "
        "Keep the exact architecture, size, window positions, lighting, and perspective unchanged. "
        "Photorealistic."
    )


def get_design_prompt(style, room_type):
    """Generate prompt for furnishing a room in a specific style.
    
    Args:
        style: Interior design style (e.g., 'Nordic', 'Modern')
        room_type: Type of room (e.g., 'Living Room', 'Bedroom')
    
    Returns:
        Formatted prompt string
    """
    return (
        f"Furnish this empty room as a {style} {room_type}. "
        "Keep the exact architecture, size, window positions, lighting, and perspective unchanged. "
        "Add furniture, rugs, and decor matching the style. Photorealistic."
    )


def get_refine_prompt(instruction):
    """Generate prompt for refining an existing design.
    
    Args:
        instruction: User's refinement instruction
    
    Returns:
        Formatted prompt string
    """
    return (
        f"Based on this image, apply the following change: {instruction}. "
        "Maintain the exact perspective, lighting, architecture, and all other furniture/decor that is not being changed. "
        "Photorealistic."
    )

