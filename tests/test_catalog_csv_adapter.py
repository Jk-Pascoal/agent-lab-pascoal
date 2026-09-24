"""Testes para o adaptador de ingestão de catálogo CSV (Slices 1 e 2)."""

import csv
import tempfile
import unittest
from pathlib import Path

from agent_lab.catalog_csv_adapter import load_catalog_materials
from agent_lab.domain import MaterialRecord


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


class CatalogCsvAdapterSlice2Tests(unittest.TestCase):
    def test_load_catalog_materials_maps_all_canonical_attributes_correctly(
        self,
    ) -> None:
        csv_content = (
            "material_id,description_short,long_description,unit,manufacturer,"
            "manufacturer_part_number,material_group,status\n"
            "MAT-01,Short desc,Detailed long desc,KG,Acme Corp,PN-1234,STEEL,ACTIVE\n"
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "full_catalog.csv"
            file_path.write_text(csv_content, encoding="utf-8")
            records = load_catalog_materials(file_path)
            self.assertEqual(len(records), 1)
            record = records[0]
            self.assertEqual(record.material_id, "MAT-01")
            self.assertEqual(record.description_short, "Short desc")
            self.assertEqual(record.long_description, "Detailed long desc")
            self.assertEqual(record.unit, "KG")
            self.assertEqual(record.manufacturer, "Acme Corp")
            self.assertEqual(record.manufacturer_part_number, "PN-1234")
            self.assertEqual(record.material_group, "STEEL")
            self.assertEqual(record.status, "ACTIVE")

    def test_load_catalog_materials_defaults_omitted_optional_columns_to_empty_string(
        self,
    ) -> None:
        csv_content = "material_id,unit\nMAT-01,KG\n"
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "partial_catalog.csv"
            file_path.write_text(csv_content, encoding="utf-8")
            records = load_catalog_materials(file_path)
            self.assertEqual(len(records), 1)
            record = records[0]
            self.assertEqual(record.material_id, "MAT-01")
            self.assertEqual(record.unit, "KG")
            self.assertEqual(record.description_short, "")
            self.assertEqual(record.long_description, "")
            self.assertEqual(record.manufacturer, "")
            self.assertEqual(record.manufacturer_part_number, "")
            self.assertEqual(record.material_group, "")
            self.assertEqual(record.status, "")

    def test_load_catalog_materials_preserves_outer_whitespace_in_material_id(
        self,
    ) -> None:
        csv_content = "material_id,unit\n  MAT-001  ,KG\n"
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "whitespace_id.csv"
            file_path.write_text(csv_content, encoding="utf-8")
            records = load_catalog_materials(file_path)
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0].material_id, "  MAT-001  ")

    def test_load_catalog_materials_preserves_internal_whitespace_and_newlines_in_fields(
        self,
    ) -> None:
        csv_content = (
            'material_id,long_description\n'
            'MAT-01,"Line 1\n  Line 2 with   spaces"\n'
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "multiline_desc.csv"
            with file_path.open("w", encoding="utf-8", newline="") as file:
                file.write(csv_content)
            records = load_catalog_materials(file_path)
            self.assertEqual(len(records), 1)
            self.assertEqual(
                records[0].long_description,
                "Line 1\n  Line 2 with   spaces",
            )

    def test_load_catalog_materials_maps_empty_optional_cells_to_empty_string(
        self,
    ) -> None:
        csv_content = "material_id,description_short,unit\nMAT-01,,KG\n"
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "empty_cells.csv"
            file_path.write_text(csv_content, encoding="utf-8")
            records = load_catalog_materials(file_path)
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0].material_id, "MAT-01")
            self.assertEqual(records[0].description_short, "")
            self.assertEqual(records[0].unit, "KG")

    def test_load_catalog_materials_uses_empty_string_for_trailing_missing_fields(
        self,
    ) -> None:
        csv_content = "material_id,description_short,unit\nMAT-01\n"
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "short_row.csv"
            file_path.write_text(csv_content, encoding="utf-8")
            records = load_catalog_materials(file_path)
            self.assertEqual(len(records), 1)
            record = records[0]
            self.assertEqual(record.material_id, "MAT-01")
            self.assertEqual(record.description_short, "")
            self.assertEqual(record.unit, "")

    def test_load_catalog_materials_raises_value_error_for_row_with_excess_fields(
        self,
    ) -> None:
        csv_content = "material_id,unit\nMAT-01,KG,EXTRA_VAL\n"
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "excess_fields.csv"
            file_path.write_text(csv_content, encoding="utf-8")
            with self.assertRaises(ValueError):
                load_catalog_materials(file_path)

    def test_load_catalog_materials_raises_csv_error_for_syntactically_invalid_csv(
        self,
    ) -> None:
        csv_content = 'material_id,description_short\n"MAT-01,unclosed quote\n'
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "invalid_syntax.csv"
            file_path.write_text(csv_content, encoding="utf-8")
            with self.assertRaises(csv.Error):
                load_catalog_materials(file_path)

    def test_load_catalog_materials_preserves_physical_row_order(
        self,
    ) -> None:
        csv_content = "material_id\nMAT-Z\nMAT-A\nMAT-M\n"
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "order_test.csv"
            file_path.write_text(csv_content, encoding="utf-8")
            records = load_catalog_materials(file_path)
            ids = tuple(r.material_id for r in records)
            self.assertEqual(ids, ("MAT-Z", "MAT-A", "MAT-M"))

    def test_load_catalog_materials_returns_strictly_tuple_of_material_records(
        self,
    ) -> None:
        csv_content = "material_id\nMAT-01\nMAT-02\n"
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "tuple_type.csv"
            file_path.write_text(csv_content, encoding="utf-8")
            records = load_catalog_materials(file_path)
            self.assertIs(type(records), tuple)
            self.assertEqual(len(records), 2)
            for r in records:
                self.assertIsInstance(r, MaterialRecord)


if __name__ == "__main__":
    unittest.main()
