import logging
from typing import List
from src.content.scene_manager import Scene
from src.content.visual_generator import VisualGenerator
from src.content.ai_video_generator import AIVideoGenerator
import google.generativeai as genai
from config.settings import Config
import json

logger = logging.getLogger(__name__)


class SceneVisualCoordinator:
    """
    Coordinates visual generation for each scene.
    Selects appropriate mix of AI videos, stock videos, and AI images.
    """
    
    def __init__(self):
        self.visual_gen = VisualGenerator()
        self.ai_video_gen = AIVideoGenerator()
        
        # Initialize Gemini for query refinement
        if Config.GEMINI_API_KEY:
            genai.configure(api_key=Config.GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-flash-latest')
        else:
            self.model = None
    
    def get_visuals_for_scene(self, scene: Scene, min_visuals: int = 2) -> List[str]:
        """
        Get appropriate visuals for a scene.
        
        Strategy:
        - Intro/Conclusion scenes: Try AI video generation
        - Main scenes: Stock videos + AI images
        - Climax scenes: Best quality stock + AI video
        
        Args:
            scene: Scene object with keywords and metadata
            min_visuals: Minimum number of visuals to return
            
        Returns:
            List of paths to visual files (videos/images)
        """
        logger.info(f"Getting visuals for scene {scene.scene_id} ({scene.visual_style})")
        
        visuals = []
        
        # Strategy based on visual style
        if scene.visual_style in ["intro", "conclusion", "climax"]:
            # Try AI video for important scenes
            ai_video = self._try_ai_video(scene)
            if ai_video:
                visuals.append(ai_video)
                logger.info(f"✓ Added AI video for scene {scene.scene_id}")
        
        # Get stock videos based on keywords
        stock_videos = self._get_stock_videos(scene, count=2)
        visuals.extend(stock_videos)
        
        # If we don't have enough visuals, add AI images
        if len(visuals) < min_visuals:
            needed = min_visuals - len(visuals)
            ai_images = self._get_ai_images(scene, count=needed)
            visuals.extend(ai_images)
        
        logger.info(f"Scene {scene.scene_id}: {len(visuals)} visuals ({self._count_types(visuals)})")
        
        return visuals
    
    def _try_ai_video(self, scene: Scene) -> str:
        """Try to generate AI video for scene."""
        if not self.ai_video_gen.is_available():
            return None
        
        # Create prompt from scene keywords and text
        prompt = self._create_video_prompt(scene)
        
        import os
        from config.settings import Config
        output_path = os.path.join(Config.ASSETS_DIR, f"ai_video_scene_{scene.scene_id}.mp4")
        
        return self.ai_video_gen.generate_video(prompt, output_path, duration=5)
    
    def _get_stock_videos(self, scene: Scene, count: int = 2) -> List[str]:
        """Get stock videos from Pexels."""
        # Use scene keywords for search
        queries = scene.keywords[:3]  # Top 3 keywords
        
        if not queries or any(len(q) < 4 for q in queries):
            # Refine queries if they are missing or too short/generic
            logger.info(f"Refining search queries for scene {scene.scene_id}...")
            queries = self._refine_search_queries(scene)
        
        if not queries:
            # Fallback to generic query
            queries = ["nature", "abstract"]
        
        try:
            videos = self.visual_gen.get_stock_videos(
                queries=queries,
                count=count,
                duration_min=3,
                orientation='portrait'
            )
            return videos if videos else []
        except Exception as e:
            logger.error(f"Stock video fetch failed: {e}")
            return []
    
    def _get_ai_images(self, scene: Scene, count: int = 2) -> List[str]:
        """Get AI-generated images."""
        images = []
        
        for i, keyword in enumerate(scene.keywords[:count]):
            try:
                import os
                from config.settings import Config
                output_path = os.path.join(
                    Config.ASSETS_DIR,
                    f"ai_image_scene_{scene.scene_id}_{i}.jpg"
                )
                
                # Generate image with Pollinations
                image_path = self.visual_gen.image_gen.generate_image(
                    prompt=keyword,
                    output_path=output_path
                )
                
                if image_path:
                    images.append(image_path)
            except Exception as e:
                logger.error(f"AI image generation failed: {e}")
        
        return images
    
    def _refine_search_queries(self, scene: Scene) -> List[str]:
        """Use Gemini to transform scene text/keywords into high-quality Pexels search queries."""
        if not self.model:
            return scene.keywords[:3]
            
        try:
            prompt = f"""
            Given the following video scene text and existing keywords, generate 3 highly specific, descriptive search queries for Pexels stock footage.
            The queries should be search-engine friendly (2-5 words) and describe exactly what we should SEE.
            Avoid generic words like "something", "there", "it", "dee".
            
            Scene Text: {scene.text}
            Existing Keywords: {', '.join(scene.keywords)}
            
            Return ONLY a JSON list of 3 strings.
            Example: ["dark eerie forest misty", "ancient wooden cabin exterior", "shattered glass window close up"]
            """
            
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            
            # Extract JSON
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            
            refined_queries = json.loads(text)
            if isinstance(refined_queries, list) and len(refined_queries) > 0:
                logger.info(f"  Refined queries: {refined_queries}")
                return refined_queries
                
        except Exception as e:
            logger.error(f"Query refinement failed: {e}")
            
        return scene.keywords[:3]

    def _create_video_prompt(self, scene: Scene) -> str:
        """Create AI video generation prompt from scene."""
        # Use first sentence of scene text + keywords
        first_sentence = scene.text.split('.')[0] if '.' in scene.text else scene.text
        keywords_str = ', '.join(scene.keywords[:3])
        
        prompt = f"{first_sentence}. Keywords: {keywords_str}"
        
        # Limit prompt length
        if len(prompt) > 200:
            prompt = prompt[:197] + "..."
        
        return prompt
    
    def _count_types(self, visuals: List[str]) -> str:
        """Count types of visuals for logging."""
        videos = sum(1 for v in visuals if v.endswith('.mp4'))
        images = sum(1 for v in visuals if v.endswith(('.jpg', '.jpeg', '.png')))
        return f"{videos} videos, {images} images"


if __name__ == "__main__":
    # Test visual coordinator
    from src.content.scene_manager import Scene
    
    test_scene = Scene(
        scene_id=1,
        text="Welcome to this amazing video about artificial intelligence.",
        duration=5.0,
        start_time=0.0,
        end_time=5.0,
        keywords=["artificial", "intelligence", "technology"],
        visual_style="intro"
    )
    
    coordinator = SceneVisualCoordinator()
    visuals = coordinator.get_visuals_for_scene(test_scene)
    
    print(f"Got {len(visuals)} visuals for test scene")
    for v in visuals:
        print(f"  - {v}")
