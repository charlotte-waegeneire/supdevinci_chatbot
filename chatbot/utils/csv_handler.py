"""CSV handler for Sup de Vinci applications."""

import csv
from datetime import datetime
import os
from typing import Any, Dict, List, Optional

import pandas as pd


class CandidatureCSVHandler:
    """Handler for saving and loading applications in CSV format."""

    def __init__(self, data_folder: str = "data"):
        """Initialize the CSV manager for applications.

        Args:
            data_folder: Folder where CSV files are stored (default: "data")
        """
        self.data_folder = data_folder
        self.csv_filename = "candidatures_supdevinci.csv"
        self.csv_path = os.path.join(data_folder, self.csv_filename)

        self._ensure_data_folder_exists()

        self.csv_columns = [
            "timestamp",
            "last_name",
            "first_name",
            "email",
            "phone",
            "age",
            "city",
            "candidate_type",
            "current_level",
            "origin_education",
            "it_experience",
            "target_level",
            "preferred_campus",
            "bachelor_specializations",
            "master_specializations",
            "professional_objective",
            "interested_sectors",
            "supdevinci_reason",
            "school_discovery",
            "info_needs",
            "availability",
            "specific_questions",
            "newsletter",
            "partner_contact",
        ]

    def _ensure_data_folder_exists(self):
        """Create the data folder if it doesn't exist."""
        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder)
            print(f"✅ Folder '{self.data_folder}' created.")

    def _create_csv_if_not_exists(self):
        """Create the CSV file with headers if it doesn't exist."""
        if not os.path.exists(self.csv_path):
            try:
                with open(self.csv_path, "w", newline="", encoding="utf-8") as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=self.csv_columns)
                    writer.writeheader()
                print(f"✅ CSV file created: {self.csv_path}")
            except OSError as error:
                print(f"❌ Error creating CSV file: {error}")

    def save_candidature(self, application_data: Dict[str, Any]) -> bool:
        """Save an application to the CSV file.

        Args:
            application_data: Dictionary containing the application data

        Returns:
            bool: True if the save was successful, False otherwise
        """
        try:
            self._create_csv_if_not_exists()

            csv_data = self._prepare_data_for_csv(application_data)

            with open(self.csv_path, "a", newline="", encoding="utf-8") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.csv_columns)
                writer.writerow(csv_data)

            print(
                f"✅ Application saved: {csv_data['first_name']} {csv_data['last_name']}"
            )
            return True

        except (OSError, KeyError, ValueError) as error:
            print(f"❌ Error saving application: {error}")
            return False

    def _prepare_data_for_csv(self, application_data: Dict[str, Any]) -> Dict[str, str]:
        """Prepare data for insertion into the CSV.

        Convert lists to comma-separated strings.

        Args:
            application_data: Raw application data

        Returns:
            Dict: Data formatted for CSV
        """
        csv_data = {}

        csv_data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for column in self.csv_columns:
            if column == "timestamp":
                continue

            value = application_data.get(column, "")

            if isinstance(value, list):
                csv_data[column] = "; ".join(value) if value else ""
            elif isinstance(value, bool):
                csv_data[column] = "Oui" if value else "Non"
            else:
                csv_data[column] = str(value) if value else ""

        return csv_data

    def load_all_candidatures(self) -> List[Dict[str, Any]]:
        """Load all applications from the CSV file.

        Returns:
            List[Dict]: List of all applications
        """
        try:
            if not os.path.exists(self.csv_path):
                return []

            applications = []
            with open(self.csv_path, encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)
                applications.extend(dict(row) for row in reader)

            return applications

        except (OSError, csv.Error) as error:
            print(f"❌ Error loading applications: {error}")
            return []

    def get_candidatures_as_dataframe(self) -> pd.DataFrame:
        """Return applications as a pandas DataFrame.

        Returns:
            pd.DataFrame: DataFrame containing all applications
        """
        try:
            if not os.path.exists(self.csv_path):
                return pd.DataFrame()

            return pd.read_csv(self.csv_path, encoding="utf-8")

        except (OSError, pd.errors.EmptyDataError, pd.errors.ParserError) as error:
            print(f"❌ Error loading DataFrame: {error}")
            return pd.DataFrame()

    def get_candidatures_count(self) -> int:
        """Return the total number of applications.

        Returns:
            int: Number of applications
        """
        try:
            if not os.path.exists(self.csv_path):
                return 0

            with open(self.csv_path, encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)
                return sum(1 for _ in reader)

        except (OSError, csv.Error) as error:
            print(f"❌ Error counting applications: {error}")
            return 0

    def search_candidatures(
        self, search_term: str, field: str = "email"
    ) -> List[Dict[str, Any]]:
        """Search for applications by a specific term.

        Args:
            search_term: Term to search for
            field: Field to search in (default: "email")

        Returns:
            List[Dict]: List of matching applications
        """
        try:
            all_applications = self.load_all_candidatures()

            return [
                application
                for application in all_applications
                if search_term.lower() in application.get(field, "").lower()
            ]

        except (AttributeError, TypeError) as error:
            print(f"❌ Error during search: {error}")
            return []

    def export_filtered_data(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        campus: Optional[str] = None,
        level: Optional[str] = None,
    ) -> str:
        """Export filtered data to a new CSV file.

        Args:
            start_date: Start date (format: YYYY-MM-DD)
            end_date: End date (format: YYYY-MM-DD)
            campus: Campus to filter
            level: Level to filter

        Returns:
            str: Path of the exported file
        """
        try:
            dataframe = self.get_candidatures_as_dataframe()

            if dataframe.empty:
                return ""

            # Apply filters
            if start_date:
                dataframe = dataframe[dataframe["timestamp"] >= start_date]
            if end_date:
                dataframe = dataframe[dataframe["timestamp"] <= end_date]
            if campus:
                dataframe = dataframe[dataframe["preferred_campus"] == campus]
            if level:
                dataframe = dataframe[dataframe["target_level"] == level]

            # Create export file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_filename = f"candidatures_filtered_{timestamp}.csv"
            export_path = os.path.join(self.data_folder, export_filename)

            dataframe.to_csv(export_path, index=False, encoding="utf-8")

            print(f"✅ Export successful: {export_path}")
            return export_path

        except (OSError, KeyError, ValueError) as error:
            print(f"❌ Error during export: {error}")
            return ""

    def get_statistics(self) -> Dict[str, Any]:
        """Generate statistics on applications.

        Returns:
            Dict: Various statistics
        """
        try:
            dataframe = self.get_candidatures_as_dataframe()

            if dataframe.empty:
                return {}

            stats = self._calculate_basic_stats(dataframe)
            stats.update(self._calculate_distribution_stats(dataframe))
            stats.update(self._calculate_additional_stats(dataframe))

            return stats

        except (KeyError, ValueError, TypeError) as error:
            print(f"❌ Error calculating statistics: {error}")
            return {}

    def _calculate_basic_stats(self, dataframe: pd.DataFrame) -> Dict[str, Any]:
        """Calculate basic statistics from DataFrame.

        Args:
            dataframe: DataFrame containing application data

        Returns:
            Dict: Basic statistics
        """
        return {
            "total_candidatures": len(dataframe),
            "latest_candidature": (
                dataframe["timestamp"].max() if "timestamp" in dataframe.columns else ""
            ),
        }

    def _calculate_distribution_stats(self, dataframe: pd.DataFrame) -> Dict[str, Any]:
        """Calculate distribution statistics from DataFrame.

        Args:
            dataframe: DataFrame containing application data

        Returns:
            Dict: Distribution statistics
        """
        return {
            "candidatures_par_campus": (
                dataframe["preferred_campus"].value_counts().to_dict()
                if "preferred_campus" in dataframe.columns
                else {}
            ),
            "candidatures_par_niveau": (
                dataframe["target_level"].value_counts().to_dict()
                if "target_level" in dataframe.columns
                else {}
            ),
            "candidatures_par_experience": (
                dataframe["it_experience"].value_counts().to_dict()
                if "it_experience" in dataframe.columns
                else {}
            ),
        }

    def _calculate_additional_stats(self, dataframe: pd.DataFrame) -> Dict[str, Any]:
        """Calculate additional statistics from DataFrame.

        Args:
            dataframe: DataFrame containing application data

        Returns:
            Dict: Additional statistics
        """
        stats = {}

        if "age" in dataframe.columns:
            try:
                numeric_ages = pd.to_numeric(dataframe["age"], errors="coerce")
                stats["age_moyen"] = numeric_ages.mean()
            except (ValueError, TypeError):
                stats["age_moyen"] = 0
        else:
            stats["age_moyen"] = 0

        if "newsletter" in dataframe.columns:
            stats["newsletter_opt_in"] = (
                dataframe["newsletter"].value_counts().get("Oui", 0)
            )
        else:
            stats["newsletter_opt_in"] = 0

        return stats
