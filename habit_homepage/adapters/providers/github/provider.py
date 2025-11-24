from enum import Enum

import requests

from habit_homepage.config.logging import get_logger
from habit_homepage.domain.habit import Habit
from habit_homepage.domain.value_objects import ProviderType
from habit_homepage.ports.providers.habit_data_provider import HabitDataProvider

logger = get_logger(__name__)


class GitHubMetric(Enum):
    """
    Enum for GitHub-specific metrics that can be tracked.
    Provides type safety for metric names in provider configuration.
    """

    CONTRIBUTIONS = "contributions"  # Total contributions (commits + PRs + issues)


class GitHubHabitDataProvider(HabitDataProvider):
    """
    Adapter for fetching data from GitHub.

    Uses GitHub's REST API v3.
    Requires a personal access token for authentication.
    """

    def __init__(self, token: str, username: str) -> None:
        """
        Initialize GitHub provider.

        Args:
            token: GitHub personal access token (for authentication)
            username: GitHub username to track
        """
        self.token = token
        self.username = username
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        }

    @property
    def provider_name(self) -> str:
        return ProviderType.GITHUB.value

    def fetch_data(self, habit: Habit, date: str) -> float | None:
        """
        Fetch data from GitHub based on the habit configuration.

        Returns total contributions for the date (commits + PRs + issues).
        This matches the GitHub contribution graph visualization.
        """
        if not habit.provider_config:
            return None

        metric_str = habit.provider_config.get("metric")
        if not metric_str:
            return None

        try:
            metric = GitHubMetric(metric_str)
        except ValueError:
            logger.warning("Unknown GitHub metric: %s", metric_str)
            return None

        if metric == GitHubMetric.CONTRIBUTIONS:
            return self._get_total_contributions(date)

        return None

    def _get_total_contributions(self, date: str) -> float:
        """
        Fetch total contributions for a specific date.

        Contributions include:
        - Commits
        - Pull requests created
        - Issues created

        This matches the GitHub contribution graph visualization.
        """
        total = 0.0

        # Get commits
        try:
            query = f"author:{self.username} committer-date:{date}"
            url = f"{self.base_url}/search/commits"
            params = {"q": query, "per_page": 1}

            response = requests.get(
                url, headers=self.headers, params=params, timeout=10
            )
            response.raise_for_status()
            data = response.json()
            total += float(data.get("total_count", 0))

        except requests.RequestException as e:
            logger.error("Error fetching GitHub commits for %s: %s", date, e)

        # Get pull requests created
        try:
            query = f"author:{self.username} type:pr created:{date}"
            url = f"{self.base_url}/search/issues"
            params = {"q": query, "per_page": 1}

            response = requests.get(
                url, headers=self.headers, params=params, timeout=10
            )
            response.raise_for_status()
            data = response.json()
            total += float(data.get("total_count", 0))

        except requests.RequestException as e:
            logger.error("Error fetching GitHub PRs for %s: %s", date, e)

        # Get issues created
        try:
            query = f"author:{self.username} type:issue created:{date}"
            url = f"{self.base_url}/search/issues"
            params = {"q": query, "per_page": 1}

            response = requests.get(
                url, headers=self.headers, params=params, timeout=10
            )
            response.raise_for_status()
            data = response.json()
            total += float(data.get("total_count", 0))

        except requests.RequestException as e:
            logger.error("Error fetching GitHub issues for %s: %s", date, e)

        return total
