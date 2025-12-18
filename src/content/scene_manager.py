import logging
import re
import json
import google.generativeai as genai
from typing import List, Dict
from dataclasses import dataclass
from config.settings import Config

logger = logging.getLogger(__name__)


@dataclass
class Scene:
    """Represents a single scene in the video."""
    scene_id: int
    text: str
    duration: float
    start_time: float
    end_time: float
    keywords: List[str]
    visual_style: str  # "intro", "main", "climax", "conclusion"


class SceneManager:
    """
    Manages script-to-scene segmentation for video generation.
    Breaks down scripts into logical scenes with timing and metadata.
    """
    
    def __init__(self, min_scene_duration=5, max_scene_duration=10):
        """
        Initialize SceneManager.
        
        Args:
            min_scene_duration: Minimum duration for a scene in seconds
            max_scene_duration: Maximum duration for a scene in seconds
        """
        self.min_scene_duration = min_scene_duration
        self.max_scene_duration = max_scene_duration
        
        # Initialize Gemini
        if Config.GEMINI_API_KEY:
            genai.configure(api_key=Config.GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-flash-latest')
        else:
            self.model = None
    
    def parse_script_to_scenes(self, script: str, target_duration: int = 60, pre_generated_scenes: List[Dict] = None) -> List[Scene]:
        """
        Parse a script into logical scenes.
        
        Args:
            script: The full script text
            target_duration: Target total video duration in seconds
            pre_generated_scenes: Optional list of scenes with text and keywords from UnifiedContentGenerator
            
        Returns:
            List of Scene objects
        """
        logger.info(f"Parsing script into scenes (target duration: {target_duration}s)")
        
        if not script:
            logger.error("Script is empty or None")
            return []
            
        if pre_generated_scenes:
            logger.info("Using pre-generated scenes and keywords...")
            return self._create_scenes_from_pre_generated(pre_generated_scenes, target_duration)

        # Split script into sentences
        sentences = self._split_into_sentences(script)
        
        if not sentences:
            logger.error("No sentences found in script")
            return []
        
        # Group sentences into scenes
        scene_groups = self._group_sentences_into_scenes(sentences, target_duration)
        
        # Create Scene objects with timing
        scenes = self._create_scenes_with_timing(scene_groups, target_duration)
        
        # Enhance with AI keywords if available
        if self.model:
            scenes = self._enhance_scenes_with_ai(scenes)
        
        logger.info(f"Created {len(scenes)} scenes from script")
        return scenes
    
    def _create_scenes_from_pre_generated(self, pre_generated_scenes: List[Dict], target_duration: int) -> List[Scene]:
        """Create Scene objects from pre-generated data."""
        scenes = []
        
        # Calculate total words
        total_words = sum(len(s["text"].split()) for s in pre_generated_scenes)
        time_per_word = target_duration / total_words if total_words > 0 else 0
        
        current_time = 0.0
        for idx, s in enumerate(pre_generated_scenes):
            text = s["text"]
            word_count = len(text.split())
            duration = word_count * time_per_word
            
            scene = Scene(
                scene_id=idx + 1,
                text=text,
                duration=duration,
                start_time=current_time,
                end_time=current_time + duration,
                keywords=s.get("keywords", []),
                visual_style=self._determine_visual_style(idx, len(pre_generated_scenes))
            )
            scenes.append(scene)
            current_time += duration
            
        return self._adjust_scene_timing(scenes, target_duration)

    def _enhance_scenes_with_ai(self, scenes: List[Scene]) -> List[Scene]:
        """Use Gemini to generate better visual keywords for each scene."""
        try:
            logger.info("Enhancing scene visuals with AI...")
            
            # Prepare prompt
            scenes_text = "\n".join([f"Scene {s.scene_id}: {s.text}" for s in scenes])
            
            prompt = f"""
            Analyze the following video script scenes and provide 3 highly specific, visual search terms for stock footage for EACH scene.
            The search terms should describe what we should SEE, not abstract concepts.
            Avoid generic words like "something", "there", "it".
            Use concrete nouns and adjectives (e.g., "dark stormy ocean", "scared woman face", "ancient library books").
            
            Script:
            {scenes_text}
            
            Return ONLY a JSON object mapping scene IDs to a list of 3 keywords/phrases.
            Format: {{"1": ["keyword1", "keyword2", "keyword3"], "2": [...]}}
            """
            
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            
            # Extract JSON
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
                
            keywords_map = json.loads(text)
            
            # Update scenes
            for scene in scenes:
                sid = str(scene.scene_id)
                if sid in keywords_map:
                    # Combine AI keywords with existing ones (prioritizing AI)
                    ai_keywords = keywords_map[sid]
                    scene.keywords = ai_keywords + scene.keywords
                    # Keep top 5
                    scene.keywords = scene.keywords[:5]
                    logger.info(f"  Scene {sid} AI keywords: {ai_keywords}")
            
            return scenes
            
        except Exception as e:
            logger.error(f"AI visual enhancement failed: {e}")
            return scenes

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Split on sentence-ending punctuation
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # Clean and filter
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    def _group_sentences_into_scenes(self, sentences: List[str], target_duration: int) -> List[List[str]]:
        """
        Group sentences into scenes based on duration and logical breaks.
        
        Strategy:
        - Aim for 5-10 second scenes
        - Group related sentences together
        - Ensure even distribution across target duration
        """
        # Estimate words per second (average speaking rate: ~2.5 words/sec)
        words_per_second = 2.5
        
        # Calculate target words per scene
        target_words_per_scene = int(self.max_scene_duration * words_per_second)
        min_words_per_scene = int(self.min_scene_duration * words_per_second)
        
        scene_groups = []
        current_group = []
        current_word_count = 0
        
        for sentence in sentences:
            words_in_sentence = len(sentence.split())
            
            # Add sentence to current group
            current_group.append(sentence)
            current_word_count += words_in_sentence
            
            # Check if we should close this scene
            should_close = False
            
            # Close if we've reached target words
            if current_word_count >= target_words_per_scene:
                should_close = True
            
            # Close if this is the last sentence
            elif sentence == sentences[-1]:
                should_close = True
            
            # Close if next sentence would make it too long
            elif sentences.index(sentence) < len(sentences) - 1:
                next_sentence = sentences[sentences.index(sentence) + 1]
                next_words = len(next_sentence.split())
                if current_word_count + next_words > target_words_per_scene * 1.3:
                    should_close = True
            
            if should_close and current_word_count >= min_words_per_scene:
                scene_groups.append(current_group)
                current_group = []
                current_word_count = 0
        
        # Add any remaining sentences
        if current_group:
            # If it's too short, merge with previous scene
            if scene_groups and current_word_count < min_words_per_scene:
                scene_groups[-1].extend(current_group)
            else:
                scene_groups.append(current_group)
        
        return scene_groups
    
    def _create_scenes_with_timing(self, scene_groups: List[List[str]], target_duration: int) -> List[Scene]:
        """Create Scene objects with accurate timing."""
        scenes = []
        
        # Calculate total words
        total_words = sum(
            sum(len(sentence.split()) for sentence in group)
            for group in scene_groups
        )
        
        # Calculate time per word based on target duration
        time_per_word = target_duration / total_words if total_words > 0 else 0
        
        current_time = 0.0
        
        for idx, group in enumerate(scene_groups):
            # Combine sentences in this group
            scene_text = ' '.join(group)
            
            # Calculate duration based on word count
            word_count = len(scene_text.split())
            scene_duration = word_count * time_per_word
            
            # Ensure minimum duration
            scene_duration = max(scene_duration, self.min_scene_duration)
            
            # Extract keywords (nouns and important words)
            keywords = self._extract_keywords(scene_text)
            
            # Determine visual style
            visual_style = self._determine_visual_style(idx, len(scene_groups))
            
            # Create scene
            scene = Scene(
                scene_id=idx + 1,
                text=scene_text,
                duration=scene_duration,
                start_time=current_time,
                end_time=current_time + scene_duration,
                keywords=keywords,
                visual_style=visual_style
            )
            
            scenes.append(scene)
            current_time += scene_duration
        
        # Adjust timing to match target duration exactly
        scenes = self._adjust_scene_timing(scenes, target_duration)
        
        return scenes
    
    def _extract_keywords(self, text: str, max_keywords: int = 5) -> List[str]:
        """
        Extract important keywords from text for visual generation.
        Simple implementation using common words and length filtering.
        """
        # Common stop words to exclude
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
            'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these',
            'those', 'it', 'its', 'they', 'them', 'their', 'something', 'there',
            'here', 'what', 'when', 'where', 'why', 'how', 'all', 'any', 'both',
            'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor',
            'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very'
        }
        
        # Extract words
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        
        # Filter and score words
        word_scores = {}
        for word in words:
            if word not in stop_words and len(word) > 3:
                # Score based on length and frequency
                word_scores[word] = word_scores.get(word, 0) + len(word)
        
        # Get top keywords
        keywords = sorted(word_scores.items(), key=lambda x: x[1], reverse=True)
        keywords = [word for word, score in keywords[:max_keywords]]
        
        return keywords
    
    def _determine_visual_style(self, scene_index: int, total_scenes: int) -> str:
        """Determine the visual style for a scene based on its position."""
        if scene_index == 0:
            return "intro"
        elif scene_index == total_scenes - 1:
            return "conclusion"
        elif scene_index == total_scenes // 2:
            return "climax"
        else:
            return "main"
    
    def _adjust_scene_timing(self, scenes: List[Scene], target_duration: int) -> List[Scene]:
        """Adjust scene timing to match target duration exactly."""
        if not scenes:
            return scenes
        
        # Calculate current total duration
        current_duration = sum(scene.duration for scene in scenes)
        
        if current_duration == 0:
            return scenes
        
        # Calculate scaling factor
        scale_factor = target_duration / current_duration
        
        # Adjust each scene
        current_time = 0.0
        for scene in scenes:
            scene.duration *= scale_factor
            scene.start_time = current_time
            scene.end_time = current_time + scene.duration
            current_time += scene.duration
        
        return scenes
    
    def get_scene_summary(self, scenes: List[Scene]) -> str:
        """Get a human-readable summary of scenes."""
        summary = f"Total Scenes: {len(scenes)}\n"
        summary += "=" * 60 + "\n\n"
        
        for scene in scenes:
            summary += f"Scene {scene.scene_id} ({scene.visual_style.upper()})\n"
            summary += f"  Time: {scene.start_time:.1f}s - {scene.end_time:.1f}s ({scene.duration:.1f}s)\n"
            summary += f"  Keywords: {', '.join(scene.keywords)}\n"
            summary += f"  Text: {scene.text[:80]}{'...' if len(scene.text) > 80 else ''}\n"
            summary += "\n"
        
        return summary


if __name__ == "__main__":
    # Test the SceneManager
    test_script = """
    Welcome to this amazing video about artificial intelligence. 
    AI is transforming the world in incredible ways. 
    From healthcare to entertainment, the possibilities are endless. 
    Machine learning algorithms can now recognize patterns that humans might miss.
    Deep learning has revolutionized computer vision and natural language processing.
    The future of AI holds even more exciting developments.
    Let's explore how this technology is shaping our future.
    """
    
    manager = SceneManager()
    scenes = manager.parse_script_to_scenes(test_script, target_duration=30)
    
    print(manager.get_scene_summary(scenes))
