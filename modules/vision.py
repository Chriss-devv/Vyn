"""
VYN v1.0 - Vision Analyzer
Image analysis using Llava model.
"""

import logging
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class VisionAnalyzer:
    """
    Analyzes images using Llava vision model.
    """
    
    VALID_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp']
    
    def __init__(self, model_manager=None):
        self.model_manager = model_manager
    
    def is_image_path(self, text: str) -> Optional[str]:
        """
        Detects if text contains a path to an image file.
        
        Args:
            text: Input text to check
            
        Returns:
            Image path if found, None otherwise
        """
        words = text.split()
        
        for word in words:
            # Check if looks like a path
            if '/' in word or '\\' in word:
                path = Path(word)
                if path.suffix.lower() in self.VALID_EXTENSIONS:
                    if path.exists():
                        return str(path.absolute())
        
        return None
    
    def analyze_image(
        self,
        image_path: str,
        prompt: Optional[str] = None,
        context: str = "general"
    ) -> str:
        """
        Analyzes an image using the vision model.
        
        Args:
            image_path: Path to image file
            prompt: Optional specific prompt for analysis
            context: Context type (general, error, diagram)
            
        Returns:
            Analysis result
        """
        if not self.model_manager:
            return "Vision analysis not available - no model manager configured"
        
        # Check if file exists
        if not Path(image_path).exists():
            return f"Image file not found: {image_path}"
        
        # Build appropriate prompt based on context
        if not prompt:
            if context == "error":
                prompt = """Analiza esta captura de pantalla de error. 
                
Identifica:
1. El tipo de error
2. La causa probable
3. Los pasos para solucionarlo

Sé específico y técnico."""
            elif context == "diagram":
                prompt = """Describe este diagrama en detalle.

Explica:
1. Los componentes principales
2. Las relaciones entre ellos
3. El flujo o arquitectura general"""
            else:
                prompt = "Analiza esta imagen en detalle. Describe lo que ves y cualquier información relevante."
        
        try:
            # Use vision model
            logger.info(f"[VYN] Analyzing image: {image_path}")
            
            # Note: Ollama's Python library would need updated for image support
            # This is a placeholder for the actual implementation
            response = f"""[Vision analysis for: {image_path}]

{prompt}

(Implementation note: This requires Ollama Python library with vision model support)
"""
            
            return response
            
        except Exception as e:
            logger.error(f"[VYN] Vision analysis failed: {e}")
            return f"Error analyzing image: {e}"
