"""Career mode for procedural sight-reading challenges.

Tracks player progression through venues with a fan-based system.
Players build their fanbase through good performances and lose fans
when they bomb. Career ends when fans hit zero.
"""

from enum import Enum
from dataclasses import dataclass, field
from procedural_songs import TIER_CONFIGS

class SetResult(Enum):
    """Result of playing a set."""
    BOMBED = "bombed"           # < 55% - lose fans, retry
    DECENT = "decent"           # 55-79% - no change, advance
    GREAT = "great"             # 80-94% - gain fans, advance
    LEGENDARY = "legendary"     # 95%+ - big fan gain, can skip


@dataclass
class Career:
    """Tracks player's career progression through procedural venues.

    Attributes:
        fans: Current fan count (0 = career over)
        current_venue: Current venue tier (1-5)
        current_set: Current set within venue (0-indexed)
        venues_unlocked: Highest venue tier unlocked
        active: Whether a career run is in progress
        can_skip_next: Whether player earned a skip from legendary performance
        sets_completed: Dict tracking which sets are completed per venue
    """
    fans: int = 100
    current_venue: int = 1
    current_set: int = 0
    venues_unlocked: int = 1
    active: bool = False
    can_skip_next: bool = False
    sets_completed: dict = field(default_factory=dict)

    # Fan rewards/penalties
    STARTING_FANS = 100
    FANS_LOST_ON_BOMB = 30
    FANS_GAINED_GREAT = 20
    FANS_GAINED_LEGENDARY = 50
    FANS_VENUE_COMPLETE_BONUS = 100

    # Score thresholds
    THRESHOLD_DECENT = 0.55      # 55% - Gold trophy
    THRESHOLD_GREAT = 0.80       # 80% - Platinum trophy
    THRESHOLD_LEGENDARY = 0.95   # 95% - Diamond trophy

    def start_new_career(self):
        """Begin a fresh career run."""
        self.fans = self.STARTING_FANS
        self.current_venue = 1
        self.current_set = 0
        self.venues_unlocked = 1
        self.active = True
        self.can_skip_next = False
        self.sets_completed = {1: set()}

    def get_result_for_score(self, score_percent: float) -> SetResult:
        """Determine the result category for a score percentage.
        Args:
            score_percent: Score as a decimal (0.0 to 1.0)
        Returns:
            SetResult enum value
        """
        if score_percent >= self.THRESHOLD_LEGENDARY:
            return SetResult.LEGENDARY
        elif score_percent >= self.THRESHOLD_GREAT:
            return SetResult.GREAT
        elif score_percent >= self.THRESHOLD_DECENT:
            return SetResult.DECENT
        else:
            return SetResult.BOMBED

    def process_set_result(self, score_percent: float, num_sets_in_venue: int) -> dict:
        """Process the result of playing a set and update career state.
        Args:
            score_percent: Score as a decimal (0.0 to 1.0)
            num_sets_in_venue: Total number of sets in current venue
        Returns:
            Dict with result info:
                - result: SetResult enum
                - fan_change: How fans changed (+/-)
                - fans: New fan count
                - advance: Whether player advances to next set
                - venue_complete: Whether venue was just completed
                - career_over: Whether career ended (fans = 0)
                - unlocked_venue: New venue tier if one was unlocked, else None
        """
        if not self.active:
            return {"error": "No active career"}

        result = self.get_result_for_score(score_percent)
        fan_change = 0
        advance = False
        venue_complete = False
        career_over = False
        unlocked_venue = None

        if result == SetResult.BOMBED:
            fan_change = -self.FANS_LOST_ON_BOMB
            self.fans = max(0, self.fans + fan_change)
            if self.fans == 0:
                career_over = True
                self.active = False
            # Don't advance - player must retry (with regenerated song)

        elif result == SetResult.DECENT:
            # No fan change, but advance
            advance = True
            self._mark_set_completed()

        elif result == SetResult.GREAT:
            fan_change = self.FANS_GAINED_GREAT
            self.fans += fan_change
            advance = True
            self._mark_set_completed()

        elif result == SetResult.LEGENDARY:
            fan_change = self.FANS_GAINED_LEGENDARY
            self.fans += fan_change
            advance = True
            self.can_skip_next = True
            self._mark_set_completed()

        # Handle advancement
        if advance:
            self.current_set += 1

            # Check if venue is complete
            if self.current_set >= num_sets_in_venue:
                venue_complete = True
                fan_change += self.FANS_VENUE_COMPLETE_BONUS
                self.fans += self.FANS_VENUE_COMPLETE_BONUS

                # Unlock next venue if available
                if self.current_venue < 5:
                    self.current_venue += 1
                    self.venues_unlocked = max(self.venues_unlocked, self.current_venue)
                    self.current_set = 0
                    self.sets_completed[self.current_venue] = set()
                    unlocked_venue = self.current_venue
                else:
                    # Completed World Tour - career complete!
                    self.active = False

        return {
            "result": result,
            "fan_change": fan_change,
            "fans": self.fans,
            "advance": advance,
            "venue_complete": venue_complete,
            "career_over": career_over,
            "unlocked_venue": unlocked_venue,
            "can_skip": self.can_skip_next if result == SetResult.LEGENDARY else False,
        }

    def _mark_set_completed(self):
        """Mark the current set as completed."""
        if self.current_venue not in self.sets_completed:
            self.sets_completed[self.current_venue] = set()
        self.sets_completed[self.current_venue].add(self.current_set)

    def use_skip(self, num_sets_in_venue: int) -> bool:
        """Use earned skip to advance past next set.

        Args:
            num_sets_in_venue: Total sets in current venue

        Returns:
            True if skip was used successfully
        """
        if not self.can_skip_next:
            return False

        self.can_skip_next = False
        self.current_set += 1
        self._mark_set_completed()

        # Check if this completes the venue
        if self.current_set >= num_sets_in_venue:
            self.fans += self.FANS_VENUE_COMPLETE_BONUS
            if self.current_venue < 5:
                self.current_venue += 1
                self.venues_unlocked = max(self.venues_unlocked, self.current_venue)
                self.current_set = 0
                self.sets_completed[self.current_venue] = set()

        return True

    def is_venue_unlocked(self, venue_tier: int) -> bool:
        """Check if a venue is unlocked.
        Args:
            venue_tier: Venue tier to check (1-5)
        Returns:
            True if venue is unlocked
        """
        return venue_tier <= self.venues_unlocked

    def is_set_unlocked(self, venue_tier: int, set_index: int) -> bool:
        """Check if a specific set is available to play.
        Args:
            venue_tier: Venue tier (1-5)
            set_index: Set index within venue (0-indexed)
        Returns:
            True if set is unlocked (current or completed)
        """
        if not self.is_venue_unlocked(venue_tier):
            return False

        if venue_tier < self.current_venue:
            # Previous venues - all sets unlocked
            return True
        elif venue_tier == self.current_venue:
            # Current venue - unlocked if current or completed
            completed = self.sets_completed.get(venue_tier, set())
            return set_index <= self.current_set or set_index in completed
        else:
            # Future venue - not unlocked
            return False

    def is_set_completed(self, venue_tier: int, set_index: int) -> bool:
        """Check if a specific set has been completed.
        Args:
            venue_tier: Venue tier (1-5)
            set_index: Set index within venue (0-indexed)
        Returns:
            True if set was completed
        """
        completed = self.sets_completed.get(venue_tier, set())
        return set_index in completed

    def get_status_text(self) -> str:
        """Get a human-readable status string.
        Returns:
            Status text like "Open Mic Night - Set 3 | 150 fans"
        """
        if not self.active:
            if self.fans == 0:
                return "Career Over - No fans left"
            elif self.current_venue > 5 or (self.current_venue == 5 and self.is_venue_complete(5)):
                return f"World Tour Complete! | {self.fans} fans"
            else:
                return "No active career"

        venue_name = TIER_CONFIGS[self.current_venue]["album_name"]
        return f"{venue_name} - Set {self.current_set + 1} | {self.fans} fans"

    def is_venue_complete(self, venue_tier: int) -> bool:
        """Check if all sets in a venue are completed.
        Args:
            venue_tier: Venue tier to check
        Returns:
            True if venue is complete
        """
        if venue_tier not in TIER_CONFIGS:
            return False

        num_sets = TIER_CONFIGS[venue_tier]["num_sets"]
        completed = self.sets_completed.get(venue_tier, set())
        return len(completed) >= num_sets

    def to_dict(self) -> dict:
        """Convert career state to a dictionary for persistence.

        Returns:
            Dict representation of career state
        """
        return {
            "fans": self.fans,
            "current_venue": self.current_venue,
            "current_set": self.current_set,
            "venues_unlocked": self.venues_unlocked,
            "active": self.active,
            "can_skip_next": self.can_skip_next,
            "sets_completed": {k: list(v) for k, v in self.sets_completed.items()},
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Career":
        """Create a Career from a dictionary.

        Args:
            data: Dict representation of career state

        Returns:
            Career instance
        """
        career = cls()
        career.fans = data.get("fans", cls.STARTING_FANS)
        career.current_venue = data.get("current_venue", 1)
        career.current_set = data.get("current_set", 0)
        career.venues_unlocked = data.get("venues_unlocked", 1)
        career.active = data.get("active", False)
        career.can_skip_next = data.get("can_skip_next", False)

        # Convert sets_completed back to sets
        sets_data = data.get("sets_completed", {})
        career.sets_completed = {int(k): set(v) for k, v in sets_data.items()}

        return career
