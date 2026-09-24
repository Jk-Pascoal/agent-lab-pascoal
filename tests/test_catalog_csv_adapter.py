"""Testes para o adaptador de ingestão de catálogo CSV (Slice 1)."""

import tempfile
import unittest
from pathlib import Path

from agent_lab.catalog_csv_adapter import load_catalog_materials


class CatalogCsvAdapterSlice1Tests(unittest.TestCase):
    def test_load_catalog_materials_raises_file_not_found_for_missing_file(
        self,
    ) -> None:
        missing_path = Path("non_existent_catalog_12345.csv")
        with self.assertRaises(FileNotFoundError):
            load_catalog_materials(missing_path)

    def test_load_catalog_materials_raises_is_a_directory_error_for_directory_path(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(IsADirectoryError):
                load_catalog_materials(temp_dir)

    def test_load_catalog_materials_raises_unicode_decode_error_for_invalid_utf8(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "invalid_utf8.csv"
            file_path.write_bytes(b"\xff\xfe\x00\x00")
            with self.assertRaises(UnicodeDecodeError):
                load_catalog_materials(file_path)

    def test_load_catalog_materials_raises_value_error_for_empty_file(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "empty.csv"
            file_path.write_text("", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_catalog_materials(file_path)

    def test_load_catalog_materials_raises_value_error_when_header_lacks_material_id(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "lacks_material_id.csv"
            file_path.write_text(
                "description_short,unit\n",
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                load_catalog_materials(file_path)

    def test_load_catalog_materials_raises_value_error_for_unrecognized_columns(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "unrecognized_col.csv"
            file_path.write_text(
                "material_id,extra_col\n",
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                load_catalog_materials(file_path)

    def test_load_catalog_materials_raises_value_error_for_duplicate_header_columns(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "duplicate_headers.csv"
            file_path.write_text(
                "material_id,unit,unit\n",
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                load_catalog_materials(file_path)

    def test_load_catalog_materials_returns_empty_tuple_for_header_only_file(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "header_only.csv"
            file_path.write_text(
                "material_id,description_short\n",
                encoding="utf-8",
            )
            result = load_catalog_materials(file_path)
            self.assertEqual(result, ())
            self.assertIsInstance(result, tuple)


if __name__ == "__main__":
    unittest.main()
