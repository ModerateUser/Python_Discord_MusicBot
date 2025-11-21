"""
Robust LLM response parser with fallback handling
Fixes critical issue where malformed LLM responses crash the bot
"""
import json
import re
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from core.exceptions import LLMResponseError, IntentParseError
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ParsedIntent:
    """Parsed natural language intent"""
    action_type: str
    parameters: Dict[str, Any]
    confidence: float = 1.0
    raw_response: Optional[str] = None


class LLMResponseParser:
    """
    Robust parser for LLM responses with multiple fallback strategies
    """
    
    # Valid action types
    VALID_ACTIONS = {
        'play', 'pause', 'resume', 'skip', 'stop', 'queue', 'volume',
        'create_playlist', 'load_playlist', 'save_playlist',
        'synthesize', 'analyze', 'similar', 'mood_playlist',
        'auto_dj', 'mood_transition', 'search'
    }
    
    def __init__(self):
        self.json_pattern = re.compile(r'\{[^{}]*\}|\[[^\[\]]*\]', re.DOTALL)
        self.code_block_pattern = re.compile(r'```(?:json)?\s*(\{.*?\})\s*```', re.DOTALL)
    
    def parse_response(self, response: str) -> ParsedIntent:
        """
        Parse LLM response with multiple fallback strategies
        
        Args:
            response: Raw LLM response
            
        Returns:
            ParsedIntent object
            
        Raises:
            LLMResponseError: If response cannot be parsed
        """
        if not response or not response.strip():
            raise LLMResponseError("Empty LLM response")
        
        response = response.strip()
        
        # Strategy 1: Direct JSON parsing
        try:
            return self._parse_json(response)
        except Exception as e:
            logger.debug(f"Direct JSON parsing failed: {e}")
        
        # Strategy 2: Extract JSON from code blocks
        try:
            return self._parse_code_block(response)
        except Exception as e:
            logger.debug(f"Code block parsing failed: {e}")
        
        # Strategy 3: Extract JSON with regex
        try:
            return self._parse_with_regex(response)
        except Exception as e:
            logger.debug(f"Regex parsing failed: {e}")
        
        # Strategy 4: Parse as plain text intent
        try:
            return self._parse_plain_text(response)
        except Exception as e:
            logger.debug(f"Plain text parsing failed: {e}")
        
        # All strategies failed
        raise LLMResponseError(
            "Failed to parse LLM response with all strategies",
            details={"response_preview": response[:200]}
        )
    
    def _parse_json(self, text: str) -> ParsedIntent:
        """Parse direct JSON response"""
        data = json.loads(text)
        return self._validate_and_create_intent(data, text)
    
    def _parse_code_block(self, text: str) -> ParsedIntent:
        """Extract and parse JSON from markdown code blocks"""
        match = self.code_block_pattern.search(text)
        if not match:
            raise ValueError("No code block found")
        
        json_str = match.group(1)
        data = json.loads(json_str)
        return self._validate_and_create_intent(data, text)
    
    def _parse_with_regex(self, text: str) -> ParsedIntent:
        """Extract JSON using regex pattern matching"""
        matches = self.json_pattern.findall(text)
        if not matches:
            raise ValueError("No JSON found in text")
        
        # Try each match until one parses successfully
        for match in matches:
            try:
                data = json.loads(match)
                if isinstance(data, dict) and 'action' in data:
                    return self._validate_and_create_intent(data, text)
            except json.JSONDecodeError:
                continue
        
        raise ValueError("No valid JSON with action found")
    
    def _parse_plain_text(self, text: str) -> ParsedIntent:
        """
        Parse plain text response as fallback
        Attempts to extract intent from natural language
        """
        text_lower = text.lower()
        
        # Simple keyword matching for common actions
        action_keywords = {
            'play': ['play', 'start', 'begin'],
            'pause': ['pause', 'stop temporarily'],
            'skip': ['skip', 'next'],
            'stop': ['stop', 'end', 'quit'],
            'search': ['search', 'find', 'look for'],
            'volume': ['volume', 'louder', 'quieter'],
        }
        
        detected_action = None
        for action, keywords in action_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                detected_action = action
                break
        
        if not detected_action:
            raise ValueError("Could not detect action from plain text")
        
        # Extract potential query (everything after the action keyword)
        query = text.strip()
        for keywords in action_keywords.values():
            for keyword in keywords:
                if keyword in text_lower:
                    idx = text_lower.index(keyword) + len(keyword)
                    query = text[idx:].strip()
                    break
        
        return ParsedIntent(
            action_type=detected_action,
            parameters={'query': query} if query else {},
            confidence=0.5,  # Lower confidence for plain text parsing
            raw_response=text
        )
    
    def _validate_and_create_intent(self, data: Dict[str, Any], raw: str) -> ParsedIntent:
        """
        Validate parsed data and create ParsedIntent
        
        Args:
            data: Parsed JSON data
            raw: Raw response text
            
        Returns:
            ParsedIntent object
            
        Raises:
            IntentParseError: If data is invalid
        """
        # Handle different response formats
        action = None
        parameters = {}
        
        # Format 1: {"action": "play", "parameters": {...}}
        if 'action' in data:
            action = data['action']
            parameters = data.get('parameters', {})
        
        # Format 2: {"action_type": "play", "query": "..."}
        elif 'action_type' in data:
            action = data['action_type']
            parameters = {k: v for k, v in data.items() if k != 'action_type'}
        
        # Format 3: {"intent": "play", ...}
        elif 'intent' in data:
            action = data['intent']
            parameters = {k: v for k, v in data.items() if k != 'intent'}
        
        # Format 4: Direct action with parameters
        else:
            # Try to find action in keys
            for key in data.keys():
                if key.lower() in self.VALID_ACTIONS:
                    action = key.lower()
                    parameters = data[key] if isinstance(data[key], dict) else {}
                    break
        
        if not action:
            raise IntentParseError(
                "No action found in response",
                details={"data": data}
            )
        
        # Normalize action name
        action = action.lower().strip()
        
        # Validate action type
        if action not in self.VALID_ACTIONS:
            # Try to map to valid action
            action = self._normalize_action(action)
            if action not in self.VALID_ACTIONS:
                raise IntentParseError(
                    f"Invalid action type: {action}",
                    details={"action": action, "valid_actions": list(self.VALID_ACTIONS)}
                )
        
        # Ensure parameters is a dict
        if not isinstance(parameters, dict):
            parameters = {'value': parameters}
        
        # Extract confidence if present
        confidence = float(data.get('confidence', 1.0))
        confidence = max(0.0, min(1.0, confidence))  # Clamp to [0, 1]
        
        return ParsedIntent(
            action_type=action,
            parameters=parameters,
            confidence=confidence,
            raw_response=raw
        )
    
    def _normalize_action(self, action: str) -> str:
        """
        Normalize action name to valid action type
        
        Args:
            action: Action name to normalize
            
        Returns:
            Normalized action name
        """
        # Common variations
        action_map = {
            'start': 'play',
            'begin': 'play',
            'unpause': 'resume',
            'continue': 'resume',
            'next': 'skip',
            'forward': 'skip',
            'halt': 'stop',
            'end': 'stop',
            'quit': 'stop',
            'find': 'search',
            'lookup': 'search',
            'vol': 'volume',
            'sound': 'volume',
            'make_playlist': 'create_playlist',
            'new_playlist': 'create_playlist',
            'open_playlist': 'load_playlist',
            'get_playlist': 'load_playlist',
            'generate': 'synthesize',
            'create_music': 'synthesize',
            'examine': 'analyze',
            'inspect': 'analyze',
            'related': 'similar',
            'like': 'similar',
        }
        
        return action_map.get(action.lower(), action)
    
    def parse_action_chain(self, response: str) -> List[ParsedIntent]:
        """
        Parse response that may contain multiple actions
        
        Args:
            response: Raw LLM response
            
        Returns:
            List of ParsedIntent objects
            
        Raises:
            LLMResponseError: If response cannot be parsed
        """
        if not response or not response.strip():
            raise LLMResponseError("Empty LLM response")
        
        response = response.strip()
        
        # Try to parse as JSON array
        try:
            data = json.loads(response)
            if isinstance(data, list):
                return [self._validate_and_create_intent(item, response) for item in data]
            elif isinstance(data, dict):
                # Single action
                return [self._validate_and_create_intent(data, response)]
        except json.JSONDecodeError:
            pass
        
        # Try to parse as single action
        try:
            intent = self.parse_response(response)
            return [intent]
        except LLMResponseError:
            pass
        
        # Try to split by common delimiters and parse each
        delimiters = ['\n---\n', '\n\n', '; then ', ' and then ', ' followed by ']
        for delimiter in delimiters:
            if delimiter in response:
                parts = response.split(delimiter)
                intents = []
                for part in parts:
                    try:
                        intent = self.parse_response(part.strip())
                        intents.append(intent)
                    except LLMResponseError:
                        continue
                if intents:
                    return intents
        
        raise LLMResponseError(
            "Failed to parse action chain",
            details={"response_preview": response[:200]}
        )


# Global parser instance
_parser = LLMResponseParser()


def parse_llm_response(response: str) -> ParsedIntent:
    """
    Parse LLM response (convenience function)
    
    Args:
        response: Raw LLM response
        
    Returns:
        ParsedIntent object
    """
    return _parser.parse_response(response)


def parse_llm_action_chain(response: str) -> List[ParsedIntent]:
    """
    Parse LLM response that may contain multiple actions
    
    Args:
        response: Raw LLM response
        
    Returns:
        List of ParsedIntent objects
    """
    return _parser.parse_action_chain(response)


def safe_parse_llm_response(response: str, default_action: str = 'play') -> ParsedIntent:
    """
    Safely parse LLM response with fallback to default action
    
    Args:
        response: Raw LLM response
        default_action: Default action if parsing fails
        
    Returns:
        ParsedIntent object (never raises)
    """
    try:
        return parse_llm_response(response)
    except Exception as e:
        logger.error(f"Failed to parse LLM response, using default: {e}")
        return ParsedIntent(
            action_type=default_action,
            parameters={'query': response[:100]},
            confidence=0.1,
            raw_response=response
        )
