"""
Unit tests for LLM response parser
Tests robust parsing with various response formats
"""
import pytest
import json
from utils.llm_parser import (
    parse_llm_response,
    extract_json_from_text,
    normalize_action,
    validate_action,
    LLMParseError
)


@pytest.mark.unit
class TestLLMParser:
    """Test suite for LLM response parsing"""
    
    def test_parse_valid_json(self):
        """Test parsing valid JSON response"""
        response = json.dumps({
            "actions": [
                {"action": "play", "query": "test song"}
            ]
        })
        
        result = parse_llm_response(response)
        
        assert result is not None
        assert "actions" in result
        assert len(result["actions"]) == 1
        assert result["actions"][0]["action"] == "play"
    
    def test_parse_json_with_code_blocks(self):
        """Test parsing JSON wrapped in markdown code blocks"""
        response = """```json
{
    "actions": [
        {"action": "play", "query": "test song"}
    ]
}
```"""
        
        result = parse_llm_response(response)
        
        assert result is not None
        assert "actions" in result
        assert result["actions"][0]["action"] == "play"
    
    def test_parse_json_with_text_prefix(self):
        """Test parsing JSON with explanatory text before it"""
        response = """Here's what I'll do:
{
    "actions": [
        {"action": "skip"}
    ]
}"""
        
        result = parse_llm_response(response)
        
        assert result is not None
        assert "actions" in result
        assert result["actions"][0]["action"] == "skip"
    
    def test_parse_malformed_json(self):
        """Test parsing malformed JSON falls back gracefully"""
        response = '{"actions": [{"action": "play", "query": "test"'  # Missing closing braces
        
        result = parse_llm_response(response)
        
        # Should return default structure
        assert result is not None
        assert "actions" in result
    
    def test_parse_plain_text_action(self):
        """Test parsing plain text action commands"""
        response = "play test song"
        
        result = parse_llm_response(response)
        
        assert result is not None
        assert "actions" in result
        assert len(result["actions"]) > 0
    
    def test_parse_empty_response(self):
        """Test parsing empty response"""
        result = parse_llm_response("")
        
        assert result is not None
        assert "actions" in result
        assert isinstance(result["actions"], list)
    
    def test_parse_none_response(self):
        """Test parsing None response"""
        result = parse_llm_response(None)
        
        assert result is not None
        assert "actions" in result
    
    def test_extract_json_from_code_block(self):
        """Test extracting JSON from markdown code block"""
        text = """```json
{"test": "value"}
```"""
        
        result = extract_json_from_text(text)
        
        assert result == '{"test": "value"}'
    
    def test_extract_json_from_mixed_content(self):
        """Test extracting JSON from text with mixed content"""
        text = """Some explanation text
{"action": "play"}
More text after"""
        
        result = extract_json_from_text(text)
        
        assert '{"action": "play"}' in result
    
    def test_normalize_action_play(self):
        """Test normalizing play action variants"""
        variants = ["play", "PLAY", "Play", "p", "start"]
        
        for variant in variants:
            normalized = normalize_action(variant)
            assert normalized == "play"
    
    def test_normalize_action_skip(self):
        """Test normalizing skip action variants"""
        variants = ["skip", "SKIP", "next", "s"]
        
        for variant in variants:
            normalized = normalize_action(variant)
            assert normalized == "skip"
    
    def test_normalize_action_pause(self):
        """Test normalizing pause action variants"""
        variants = ["pause", "PAUSE", "stop", "halt"]
        
        for variant in variants:
            normalized = normalize_action(variant)
            assert normalized == "pause"
    
    def test_normalize_unknown_action(self):
        """Test normalizing unknown action returns original"""
        action = "unknown_action"
        normalized = normalize_action(action)
        
        assert normalized == "unknown_action"
    
    def test_validate_action_valid(self):
        """Test validating valid action structure"""
        action = {
            "action": "play",
            "query": "test song"
        }
        
        assert validate_action(action) is True
    
    def test_validate_action_missing_action_field(self):
        """Test validating action without action field"""
        action = {
            "query": "test song"
        }
        
        assert validate_action(action) is False
    
    def test_validate_action_empty_action(self):
        """Test validating action with empty action field"""
        action = {
            "action": "",
            "query": "test"
        }
        
        assert validate_action(action) is False
    
    def test_validate_action_not_dict(self):
        """Test validating non-dictionary action"""
        assert validate_action("not a dict") is False
        assert validate_action(None) is False
        assert validate_action([]) is False
    
    def test_parse_multiple_actions(self):
        """Test parsing response with multiple actions"""
        response = json.dumps({
            "actions": [
                {"action": "play", "query": "song 1"},
                {"action": "queue", "query": "song 2"},
                {"action": "skip"}
            ]
        })
        
        result = parse_llm_response(response)
        
        assert len(result["actions"]) == 3
        assert result["actions"][0]["action"] == "play"
        assert result["actions"][1]["action"] == "queue"
        assert result["actions"][2]["action"] == "skip"
    
    def test_parse_action_with_parameters(self):
        """Test parsing action with additional parameters"""
        response = json.dumps({
            "actions": [{
                "action": "volume",
                "value": 75,
                "reason": "User requested volume change"
            }]
        })
        
        result = parse_llm_response(response)
        
        action = result["actions"][0]
        assert action["action"] == "volume"
        assert action["value"] == 75
        assert "reason" in action
    
    def test_parse_nested_json(self):
        """Test parsing deeply nested JSON"""
        response = json.dumps({
            "actions": [{
                "action": "playlist",
                "details": {
                    "name": "test",
                    "songs": ["song1", "song2"]
                }
            }]
        })
        
        result = parse_llm_response(response)
        
        action = result["actions"][0]
        assert action["action"] == "playlist"
        assert "details" in action
        assert action["details"]["name"] == "test"
    
    def test_parse_unicode_content(self):
        """Test parsing response with unicode characters"""
        response = json.dumps({
            "actions": [{
                "action": "play",
                "query": "Test 🎵 Song 音楽"
            }]
        })
        
        result = parse_llm_response(response)
        
        assert result["actions"][0]["query"] == "Test 🎵 Song 音楽"
    
    def test_parse_escaped_characters(self):
        """Test parsing response with escaped characters"""
        response = json.dumps({
            "actions": [{
                "action": "play",
                "query": "Song with \"quotes\" and \\ backslash"
            }]
        })
        
        result = parse_llm_response(response)
        
        assert "quotes" in result["actions"][0]["query"]
    
    def test_parse_large_response(self):
        """Test parsing large response with many actions"""
        actions = [
            {"action": "play", "query": f"song {i}"}
            for i in range(100)
        ]
        response = json.dumps({"actions": actions})
        
        result = parse_llm_response(response)
        
        assert len(result["actions"]) == 100
    
    def test_parse_response_with_extra_fields(self):
        """Test parsing response with extra fields"""
        response = json.dumps({
            "actions": [{"action": "play", "query": "test"}],
            "confidence": 0.95,
            "model": "test-model",
            "extra_data": "ignored"
        })
        
        result = parse_llm_response(response)
        
        assert "actions" in result
        assert "confidence" in result
        assert result["confidence"] == 0.95


@pytest.mark.unit
class TestLLMParserEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_parse_invalid_json_structure(self):
        """Test parsing JSON with invalid structure"""
        response = json.dumps({
            "not_actions": "wrong field"
        })
        
        result = parse_llm_response(response)
        
        # Should return default structure
        assert "actions" in result
        assert isinstance(result["actions"], list)
    
    def test_parse_actions_not_list(self):
        """Test parsing when actions field is not a list"""
        response = json.dumps({
            "actions": "not a list"
        })
        
        result = parse_llm_response(response)
        
        # Should handle gracefully
        assert "actions" in result
    
    def test_parse_very_long_string(self):
        """Test parsing very long response string"""
        long_query = "a" * 10000
        response = json.dumps({
            "actions": [{"action": "play", "query": long_query}]
        })
        
        result = parse_llm_response(response)
        
        assert result is not None
        assert len(result["actions"][0]["query"]) == 10000
    
    def test_parse_special_characters(self):
        """Test parsing with special characters"""
        response = json.dumps({
            "actions": [{
                "action": "play",
                "query": "!@#$%^&*()_+-=[]{}|;:',.<>?/~`"
            }]
        })
        
        result = parse_llm_response(response)
        
        assert result["actions"][0]["query"] == "!@#$%^&*()_+-=[]{}|;:',.<>?/~`"
    
    def test_parse_null_values(self):
        """Test parsing with null values"""
        response = json.dumps({
            "actions": [{
                "action": "play",
                "query": None
            }]
        })
        
        result = parse_llm_response(response)
        
        assert result is not None
        assert "actions" in result
    
    def test_parse_mixed_valid_invalid_actions(self):
        """Test parsing mix of valid and invalid actions"""
        response = json.dumps({
            "actions": [
                {"action": "play", "query": "valid"},
                {"invalid": "structure"},
                {"action": "skip"},
                "not an object"
            ]
        })
        
        result = parse_llm_response(response)
        
        # Should filter out invalid actions
        assert "actions" in result
        valid_actions = [a for a in result["actions"] if validate_action(a)]
        assert len(valid_actions) >= 2
    
    def test_parse_whitespace_only(self):
        """Test parsing whitespace-only response"""
        result = parse_llm_response("   \n\t  ")
        
        assert result is not None
        assert "actions" in result
    
    def test_parse_json_with_comments(self):
        """Test parsing JSON with comments (invalid JSON)"""
        response = """{
            // This is a comment
            "actions": [
                {"action": "play", "query": "test"}
            ]
        }"""
        
        result = parse_llm_response(response)
        
        # Should handle gracefully
        assert result is not None
    
    def test_normalize_action_with_whitespace(self):
        """Test normalizing action with whitespace"""
        assert normalize_action("  play  ") == "play"
        assert normalize_action("\tskip\n") == "skip"
    
    def test_normalize_action_empty_string(self):
        """Test normalizing empty action string"""
        result = normalize_action("")
        assert result == ""
    
    def test_extract_json_no_json_found(self):
        """Test extracting JSON when none exists"""
        text = "This is just plain text with no JSON"
        result = extract_json_from_text(text)
        
        # Should return original text
        assert result == text
    
    def test_parse_response_with_bom(self):
        """Test parsing response with byte order mark"""
        response = '\ufeff{"actions": [{"action": "play"}]}'
        
        result = parse_llm_response(response)
        
        assert result is not None
        assert "actions" in result


@pytest.mark.unit
class TestLLMParserIntegration:
    """Integration tests for complete parsing workflows"""
    
    def test_full_parsing_workflow(self):
        """Test complete parsing workflow from raw response to validated actions"""
        raw_response = """The user wants to play music. Here's what I'll do:
```json
{
    "actions": [
        {"action": "play", "query": "test song", "reason": "User request"}
    ]
}
```"""
        
        # Parse
        result = parse_llm_response(raw_response)
        
        # Validate
        assert result is not None
        assert "actions" in result
        assert len(result["actions"]) > 0
        
        # Check action
        action = result["actions"][0]
        assert validate_action(action)
        assert action["action"] == "play"
        assert action["query"] == "test song"
    
    def test_fallback_chain(self):
        """Test that parser tries multiple fallback strategies"""
        # Completely malformed response
        response = "play some music please"
        
        result = parse_llm_response(response)
        
        # Should still return valid structure
        assert result is not None
        assert "actions" in result
        assert isinstance(result["actions"], list)
    
    def test_real_world_llm_response(self):
        """Test parsing realistic LLM response"""
        response = """I'll help you with that! Here's what I'm going to do:

```json
{
    "actions": [
        {
            "action": "play",
            "query": "Bohemian Rhapsody by Queen",
            "reason": "User requested this specific song"
        }
    ],
    "confidence": 0.98,
    "understood": true
}
```

I'll start playing that song for you now!"""
        
        result = parse_llm_response(response)
        
        assert result["actions"][0]["action"] == "play"
        assert "Queen" in result["actions"][0]["query"]
        assert result["confidence"] == 0.98
