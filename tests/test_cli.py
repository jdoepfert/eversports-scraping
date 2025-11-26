from unittest.mock import MagicMock, patch

from eversports_scraper import cli


@patch("eversports_scraper.cli.run.run")
@patch("eversports_scraper.cli.parse_arguments")
def test_main_calls_run(mock_args, mock_run):
    mock_args.return_value = MagicMock(start_date="2025-01-01", days=5, verbose=True)
    
    cli.main()
    
    mock_run.assert_called_once_with(start_date="2025-01-01", days=5)
