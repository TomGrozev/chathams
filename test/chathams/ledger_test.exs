defmodule Chathams.LedgerTest do
  use Chathams.DataCase

  alias Chathams.Ledger

  describe "sheets" do
    alias Chathams.Ledger.Sheet

    import Chathams.LedgerFixtures

    @invalid_attrs %{purchases: nil}

    test "list_sheets/0 returns all sheets" do
      sheet = sheet_fixture()

      assert [listed] = Ledger.list_sheets()
      assert listed.id == sheet.id
    end

    test "get_sheet!/1 returns the sheet with given id" do
      sheet = sheet_fixture()

      assert %Sheet{id: id} = Ledger.get_sheet!(sheet.id)
      assert id == sheet.id
    end

    test "create_sheet/1 with valid data creates a sheet" do
      valid_attrs = %{purchases: [%{purchases: [1.5]}]}

      assert {:ok, %Sheet{} = sheet} = Ledger.create_sheet(valid_attrs)
      assert [purchase] = sheet.purchases
      assert purchase.purchases == [1.5]
    end

    test "create_sheet/1 with invalid data returns error changeset" do
      assert {:error, %Ecto.Changeset{}} = Ledger.create_sheet(@invalid_attrs)
    end

    test "update_sheet/2 with valid data updates the sheet" do
      sheet = sheet_fixture()
      [purchase] = sheet.purchases
      update_attrs = %{purchases: [%{id: purchase.id, purchases: [2.5]}]}

      assert {:ok, %Sheet{} = sheet} = Ledger.update_sheet(sheet, update_attrs)
      assert [purchase] = sheet.purchases
      assert purchase.purchases == [2.5]
    end

    test "update_sheet/2 with invalid data returns error changeset" do
      sheet = sheet_fixture()

      assert {:error, %Ecto.Changeset{errors: errors}} =
               Ledger.update_sheet(sheet, @invalid_attrs)

      assert Keyword.has_key?(errors, :purchases)
    end

    test "change_sheet/1 returns a sheet changeset" do
      sheet = sheet_fixture()
      assert %Ecto.Changeset{} = Ledger.change_sheet(sheet)
    end
  end
end
