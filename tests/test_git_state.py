"""Tests for git_state module."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from automated_changelog.git_state import (
    fetch_commits,
    read_last_commit_hash,
    write_changelog_entry,
)


class TestReadLastCommitHash:
    """Tests for read_last_commit_hash function."""

    def test_read_hash_from_existing_file(self, tmp_path):
        """Test reading hash from a file with state marker."""
        changelog = tmp_path / "CHANGELOG.md"
        test_hash = "abc123def456789012345678901234567890abcd"
        content = f"<!-- CHANGELOG_STATE: {test_hash} -->\n\n## Previous entries\n"
        changelog.write_text(content)

        result = read_last_commit_hash(changelog)
        assert result == test_hash

    def test_read_hash_with_extra_whitespace(self, tmp_path):
        """Test reading hash with extra whitespace in marker."""
        changelog = tmp_path / "CHANGELOG.md"
        test_hash = "abc123def456789012345678901234567890abcd"
        content = f"<!-- CHANGELOG_STATE:   {test_hash}   -->\n\n## Previous entries\n"
        changelog.write_text(content)

        result = read_last_commit_hash(changelog)
        assert result == test_hash

    def test_read_hash_from_nonexistent_file(self, tmp_path):
        """Test reading hash when file doesn't exist."""
        changelog = tmp_path / "CHANGELOG.md"
        result = read_last_commit_hash(changelog)
        assert result is None

    def test_read_hash_from_file_without_marker(self, tmp_path):
        """Test reading hash when file exists but has no marker."""
        changelog = tmp_path / "CHANGELOG.md"
        changelog.write_text("## Some changelog\n\nNo state marker here\n")

        result = read_last_commit_hash(changelog)
        assert result is None

    def test_read_hash_with_path_string(self, tmp_path):
        """Test that function accepts string paths."""
        changelog = tmp_path / "CHANGELOG.md"
        test_hash = "abc123def456789012345678901234567890abcd"
        content = f"<!-- CHANGELOG_STATE: {test_hash} -->\n\n"
        changelog.write_text(content)

        result = read_last_commit_hash(str(changelog))
        assert result == test_hash


class TestWriteChangelogEntry:
    """Tests for write_changelog_entry function."""

    def test_write_to_new_file(self, tmp_path):
        """Test writing changelog to a new file."""
        changelog = tmp_path / "CHANGELOG.md"
        test_hash = "abc123def456789012345678901234567890abcd"
        summary = "## [2025-01-15]\n\n- New feature added\n"

        write_changelog_entry(changelog, test_hash, summary)

        assert changelog.exists()
        content = changelog.read_text()

        # Check state marker is present
        assert f"<!-- CHANGELOG_STATE: {test_hash} -->" in content
        # Check summary is present
        assert summary in content

    def test_prepend_to_existing_file(self, tmp_path):
        """Test prepending new entry to existing changelog."""
        changelog = tmp_path / "CHANGELOG.md"
        old_hash = "old1234567890123456789012345678901234567"
        old_content = f"<!-- CHANGELOG_STATE: {old_hash} -->\n\n## [2025-01-14]\n\n- Old entry\n"
        changelog.write_text(old_content)

        new_hash = "new1234567890123456789012345678901234567"
        new_summary = "## [2025-01-15]\n\n- New entry\n"

        write_changelog_entry(changelog, new_hash, new_summary)

        content = changelog.read_text()

        # Check new state marker replaces old one
        assert f"<!-- CHANGELOG_STATE: {new_hash} -->" in content
        assert f"<!-- CHANGELOG_STATE: {old_hash} -->" not in content

        # Check new summary appears before old content
        new_pos = content.find(new_summary)
        old_pos = content.find("Old entry")
        assert new_pos < old_pos

    def test_write_with_path_string(self, tmp_path):
        """Test that function accepts string paths."""
        changelog = tmp_path / "CHANGELOG.md"
        test_hash = "abc123def456789012345678901234567890abcd"
        summary = "## Test\n"

        write_changelog_entry(str(changelog), test_hash, summary)

        assert changelog.exists()

    def test_preserves_existing_content_without_marker(self, tmp_path):
        """Test that existing content without marker is preserved."""
        changelog = tmp_path / "CHANGELOG.md"
        old_content = "## [2025-01-14]\n\n- Old entry without marker\n"
        changelog.write_text(old_content)

        new_hash = "new1234567890123456789012345678901234567"
        new_summary = "## [2025-01-15]\n\n- New entry\n"

        write_changelog_entry(changelog, new_hash, new_summary)

        content = changelog.read_text()

        # Check new marker is added
        assert f"<!-- CHANGELOG_STATE: {new_hash} -->" in content
        # Check both new and old content present
        assert new_summary in content
        assert old_content.strip() in content


class TestFetchCommits:
    """Tests for fetch_commits function."""

    @patch("automated_changelog.git_state.subprocess.run")
    def test_fetch_commits_with_no_last_hash(self, mock_run):
        """Test fetching commits when no last hash provided."""
        # Mock git log output
        mock_result = MagicMock()
        mock_result.stdout = "abc123def456789012345678901234567890abcd|||a1b2c3d|||John Doe|||2025-10-27 14:32:15 -0700|||Initial commit"
        mock_run.return_value = mock_result

        # Fetch commits
        commits = fetch_commits()

        assert len(commits) == 1
        commit = commits[0]
        assert len(commit["hash"]) == 40  # Full SHA-1 hash
        assert commit["short_hash"] == "a1b2c3d"
        assert commit["author"] == "John Doe"
        assert commit["date"] == "2025-10-27 14:32"
        assert commit["subject"] == "Initial commit"

        # Verify git log was called correctly (without commit range)
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[0] == "git"
        assert "log" in args
        assert "--pretty=format:%H|||%h|||%an|||%ai|||%s" in args

    @patch("automated_changelog.git_state.subprocess.run")
    def test_fetch_commits_with_last_hash(self, mock_run):
        """Test fetching commits since a specific hash."""
        # Mock git log output
        first_hash = "abc123def456789012345678901234567890abcd"
        mock_result = MagicMock()
        mock_result.stdout = "def456789012345678901234567890abcdef456|||d4e5f67|||Jane Smith|||2025-10-26 10:15:42 -0700|||Second commit"
        mock_run.return_value = mock_result

        # Fetch commits since first hash
        commits = fetch_commits(last_commit_hash=first_hash)

        assert len(commits) == 1
        commit = commits[0]
        assert commit["subject"] == "Second commit"

        # Verify git log was called with commit range
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert f"{first_hash}..HEAD" in args

    @patch("automated_changelog.git_state.subprocess.run")
    def test_fetch_commits_returns_empty_when_no_new_commits(self, mock_run):
        """Test that fetch returns empty list when no new commits."""
        # Mock empty git log output
        head_hash = "abc123def456789012345678901234567890abcd"
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_run.return_value = mock_result

        # Fetch commits since HEAD (should be empty)
        commits = fetch_commits(last_commit_hash=head_hash)

        assert len(commits) == 0

    @patch("automated_changelog.git_state.subprocess.run")
    def test_fetch_commits_raises_on_invalid_repo(self, mock_run):
        """Test that function raises error for invalid git repo."""
        # Mock subprocess error
        mock_run.side_effect = subprocess.CalledProcessError(128, "git")

        with pytest.raises(subprocess.CalledProcessError):
            fetch_commits()

    @patch("automated_changelog.git_state.subprocess.run")
    def test_fetch_multiple_commits(self, mock_run):
        """Test fetching multiple commits."""
        # Mock multiple commits in git log output
        mock_result = MagicMock()
        mock_result.stdout = (
            "333333333333333333333333333333333333333333|||3333333|||Alice|||2025-10-24 09:20:11 -0700|||Third\n"
            "222222222222222222222222222222222222222222|||2222222|||Bob|||2025-10-23 08:15:22 -0700|||Second\n"
            "111111111111111111111111111111111111111111|||1111111|||Charlie|||2025-10-22 07:10:33 -0700|||First"
        )
        mock_run.return_value = mock_result

        # Fetch all commits
        commits = fetch_commits()

        assert len(commits) == 3
        # Commits are in reverse chronological order (newest first)
        assert commits[0]["subject"] == "Third"
        assert commits[1]["subject"] == "Second"
        assert commits[2]["subject"] == "First"


class TestIntegration:
    """Integration tests combining multiple functions."""

    @patch("automated_changelog.git_state.subprocess.run")
    def test_full_workflow(self, mock_run, tmp_path):
        """Test the complete workflow: read, fetch, write."""
        first_hash = "abc123def456789012345678901234567890abcd"
        second_hash = "def456789012345678901234567890abcdef456"

        # Write initial changelog
        changelog = tmp_path / "CHANGELOG.md"
        write_changelog_entry(
            changelog, first_hash, "## [2025-01-15]\n\n- First release\n"
        )

        # Verify we can read the hash back
        read_hash = read_last_commit_hash(changelog)
        assert read_hash == first_hash

        # Mock fetching new commits
        mock_result = MagicMock()
        mock_result.stdout = f"{second_hash}|||d4e5f67|||John|||2025-10-27 15:45:30 -0700|||Second commit"
        mock_run.return_value = mock_result

        # Fetch new commits
        new_commits = fetch_commits(last_commit_hash=read_hash)
        assert len(new_commits) == 1
        assert new_commits[0]["subject"] == "Second commit"

        # Update changelog
        write_changelog_entry(
            changelog, new_commits[0]["hash"], "## [2025-01-16]\n\n- Second release\n"
        )

        # Verify the changelog has both entries
        content = changelog.read_text()
        assert "Second release" in content
        assert "First release" in content
        # Second release should come first
        assert content.index("Second release") < content.index("First release")
