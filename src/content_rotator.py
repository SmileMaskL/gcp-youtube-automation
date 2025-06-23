# src/content_rotator.py
import logging
import random
# F401 'typing.Dict', 'typing.Union' 사용되지 않으므로 제거 (혹시 포함되어 있었다면)

logger = logging.getLogger(__name__)


class ContentRotator:
    def __init__(self, content_list):
        if not isinstance(content_list, list) or not content_list:
            raise ValueError("Content list must be a non-empty list.")
        self.content_list = content_list
        self.used_content = []
        logger.info(f"ContentRotator initialized with {len(content_list)} items.")

    def get_next_content(self):
        """
        Retrieves the next content item, ensuring variety.
        Once all content items are used, it resets and shuffles.
        """
        if not self.content_list and not self.used_content:
            raise IndexError("No content available to rotate.")

        if not self.content_list:
            logger.info("All content used, resetting and shuffling for new rotation.")
            self.content_list = self.used_content
            self.used_content = []
            random.shuffle(self.content_list)

        next_item = self.content_list.pop(0)
        self.used_content.append(next_item)
        # E501 해결: 줄 길이를 79자 이하로 맞춤
        logger.info(f"Retrieved content item. Remaining: {len(self.content_list)}, "
                    f"Used: {len(self.used_content)}")
        return next_item

    def add_content(self, new_item):
        """Adds a new content item to the rotation."""
        self.content_list.append(new_item)
        # E501 해결: 줄 길이를 79자 이하로 맞춤
        logger.info(f"New content added. Total content items: "
                    f"{len(self.content_list) + len(self.used_content)}")

    def remove_content(self, item):
        """Removes a specific content item from rotation."""
        if item in self.content_list:
            self.content_list.remove(item)
            logger.info("Content item removed from active list.")
            return True
        elif item in self.used_content:
            self.used_content.remove(item)
            logger.info("Content item removed from used list.")
            return True
        logger.warning("Content item not found in rotation lists.")
        return False
    
