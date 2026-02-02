"""Tests for backend.core.prompts module."""
import pytest
from backend.core.prompts import (
    get_empty_room_prompt,
    get_design_prompt,
    get_refine_prompt
)


class TestGetEmptyRoomPrompt:
    """Test get_empty_room_prompt function."""
    
    def test_returns_string(self):
        """Test that function returns a string."""
        result = get_empty_room_prompt()
        assert isinstance(result, str)
    
    def test_prompt_not_empty(self):
        """Test that prompt is not empty."""
        result = get_empty_room_prompt()
        assert len(result) > 0
    
    def test_prompt_contains_remove_furniture(self):
        """Test that prompt mentions removing furniture."""
        result = get_empty_room_prompt()
        assert "remove" in result.lower()
        assert "furniture" in result.lower()
    
    def test_prompt_contains_empty_room(self):
        """Test that prompt mentions empty room."""
        result = get_empty_room_prompt()
        assert "empty" in result.lower()
    
    def test_prompt_contains_keep_architecture(self):
        """Test that prompt mentions keeping architecture."""
        result = get_empty_room_prompt()
        assert "architecture" in result.lower()
        assert "unchanged" in result.lower()
    
    def test_prompt_contains_photorealistic(self):
        """Test that prompt contains photorealistic keyword."""
        result = get_empty_room_prompt()
        assert "photorealistic" in result.lower()
    
    def test_prompt_is_consistent(self):
        """Test that function returns same prompt on multiple calls."""
        result1 = get_empty_room_prompt()
        result2 = get_empty_room_prompt()
        assert result1 == result2


class TestGetDesignPrompt:
    """Test get_design_prompt function."""
    
    def test_returns_string(self):
        """Test that function returns a string."""
        result = get_design_prompt("Modern", "Living Room")
        assert isinstance(result, str)
    
    def test_prompt_not_empty(self):
        """Test that prompt is not empty."""
        result = get_design_prompt("Nordic", "Bedroom")
        assert len(result) > 0
    
    def test_prompt_contains_style(self):
        """Test that prompt includes the specified style."""
        style = "Minimalist"
        result = get_design_prompt(style, "Living Room")
        assert style in result
    
    def test_prompt_contains_room_type(self):
        """Test that prompt includes the specified room type."""
        room_type = "Dining Room"
        result = get_design_prompt("Modern", room_type)
        assert room_type in result
    
    def test_prompt_contains_furnish(self):
        """Test that prompt mentions furnishing."""
        result = get_design_prompt("Nordic", "Bedroom")
        assert "furnish" in result.lower()
    
    def test_prompt_contains_photorealistic(self):
        """Test that prompt contains photorealistic keyword."""
        result = get_design_prompt("Modern", "Living Room")
        assert "photorealistic" in result.lower()
    
    def test_prompt_without_additional_instructions(self):
        """Test prompt when no additional instructions provided."""
        result = get_design_prompt("Nordic", "Living Room")
        assert "Nordic" in result
        assert "Living Room" in result
    
    def test_prompt_with_additional_instructions(self):
        """Test prompt with additional instructions."""
        additional = "Add a fireplace and large windows"
        result = get_design_prompt("Modern", "Living Room", additional)
        assert additional in result
    
    def test_prompt_with_empty_additional_instructions(self):
        """Test that empty additional instructions are not added."""
        result = get_design_prompt("Modern", "Living Room", "")
        assert result == get_design_prompt("Modern", "Living Room", None)
    
    def test_prompt_with_whitespace_only_instructions(self):
        """Test that whitespace-only instructions are not added."""
        result = get_design_prompt("Modern", "Living Room", "   ")
        assert result == get_design_prompt("Modern", "Living Room", None)
    
    def test_prompt_strips_extra_whitespace_from_instructions(self):
        """Test that extra whitespace is stripped from instructions."""
        result = get_design_prompt("Modern", "Living Room", "  Add plants  ")
        assert "Add plants" in result
        assert "  Add plants  " not in result
    
    def test_different_styles_produce_different_prompts(self):
        """Test that different styles produce different prompts."""
        result1 = get_design_prompt("Nordic", "Living Room")
        result2 = get_design_prompt("Industrial", "Living Room")
        assert result1 != result2
        assert "Nordic" in result1
        assert "Industrial" in result2
    
    def test_different_room_types_produce_different_prompts(self):
        """Test that different room types produce different prompts."""
        result1 = get_design_prompt("Modern", "Living Room")
        result2 = get_design_prompt("Modern", "Bedroom")
        assert result1 != result2
        assert "Living Room" in result1
        assert "Bedroom" in result2


class TestGetRefinePrompt:
    """Test get_refine_prompt function."""
    
    def test_returns_string(self):
        """Test that function returns a string."""
        result = get_refine_prompt("Change the wall color to blue")
        assert isinstance(result, str)
    
    def test_prompt_not_empty(self):
        """Test that prompt is not empty."""
        result = get_refine_prompt("Add a plant")
        assert len(result) > 0
    
    def test_prompt_contains_instruction(self):
        """Test that prompt includes the user instruction."""
        instruction = "Replace the sofa with a sectional"
        result = get_refine_prompt(instruction)
        assert instruction in result
    
    def test_prompt_contains_based_on_image(self):
        """Test that prompt mentions basing changes on image."""
        result = get_refine_prompt("Add a lamp")
        assert "based on" in result.lower() or "image" in result.lower()
    
    def test_prompt_contains_maintain_perspective(self):
        """Test that prompt mentions maintaining perspective."""
        result = get_refine_prompt("Change wall color")
        assert "maintain" in result.lower() and "perspective" in result.lower()
    
    def test_prompt_contains_photorealistic(self):
        """Test that prompt contains photorealistic keyword."""
        result = get_refine_prompt("Add a rug")
        assert "photorealistic" in result.lower()
    
    def test_different_instructions_produce_different_prompts(self):
        """Test that different instructions produce different prompts."""
        result1 = get_refine_prompt("Add a plant")
        result2 = get_refine_prompt("Change wall color")
        assert result1 != result2
        assert "Add a plant" in result1
        assert "Change wall color" in result2
    
    def test_prompt_with_long_instruction(self):
        """Test prompt with a long detailed instruction."""
        long_instruction = (
            "Replace the current sofa with a modern sectional in gray fabric, "
            "add two accent chairs in navy blue, and place a round coffee table "
            "in the center with decorative books and a small plant"
        )
        result = get_refine_prompt(long_instruction)
        assert long_instruction in result
    
    def test_prompt_with_short_instruction(self):
        """Test prompt with a very short instruction."""
        short_instruction = "Add lamp"
        result = get_refine_prompt(short_instruction)
        assert short_instruction in result
    
    def test_prompt_with_special_characters(self):
        """Test prompt with special characters in instruction."""
        instruction = "Add a 36\" TV above the fireplace"
        result = get_refine_prompt(instruction)
        assert instruction in result


class TestPromptFunctionSignatures:
    """Test function signatures and parameters."""
    
    def test_get_empty_room_prompt_no_params(self):
        """Test that get_empty_room_prompt takes no parameters."""
        # Should not raise
        get_empty_room_prompt()
    
    def test_get_design_prompt_requires_style_and_room(self):
        """Test that get_design_prompt requires style and room_type."""
        with pytest.raises(TypeError):
            get_design_prompt()
        
        with pytest.raises(TypeError):
            get_design_prompt("Modern")
    
    def test_get_design_prompt_optional_instructions(self):
        """Test that get_design_prompt has optional additional_instructions."""
        # Should not raise
        get_design_prompt("Modern", "Living Room")
        get_design_prompt("Modern", "Living Room", "Add plants")
    
    def test_get_refine_prompt_requires_instruction(self):
        """Test that get_refine_prompt requires instruction parameter."""
        with pytest.raises(TypeError):
            get_refine_prompt()


class TestPromptConsistency:
    """Test consistency and structure of prompts."""
    
    def test_all_prompts_are_non_empty_strings(self):
        """Test that all prompt functions return non-empty strings."""
        empty_prompt = get_empty_room_prompt()
        design_prompt = get_design_prompt("Modern", "Living Room")
        refine_prompt = get_refine_prompt("Add plants")
        
        assert isinstance(empty_prompt, str) and len(empty_prompt) > 0
        assert isinstance(design_prompt, str) and len(design_prompt) > 0
        assert isinstance(refine_prompt, str) and len(refine_prompt) > 0
    
    def test_all_prompts_contain_photorealistic(self):
        """Test that all prompts contain photorealistic keyword."""
        empty_prompt = get_empty_room_prompt()
        design_prompt = get_design_prompt("Modern", "Living Room")
        refine_prompt = get_refine_prompt("Add plants")
        
        assert "photorealistic" in empty_prompt.lower()
        assert "photorealistic" in design_prompt.lower()
        assert "photorealistic" in refine_prompt.lower()
