defmodule Chathams.LedgerTest do
  use Chathams.DataCase

  alias Chathams.Ledger

  describe "sheets" do
    alias Chathams.Ledger.Sheet

    import Chathams.LedgerFixtures

    @invalid_attrs %{purchases: nil}

    test "list_sheets/0 returns all sheets" do
      sheet = sheet_fixture()
      assert Ledger.list_sheets() == [sheet]
    end

    test "get_sheet!/1 returns the sheet with given id" do
      sheet = sheet_fixture()
      assert Ledger.get_sheet!(sheet.id) == sheet
    end

    test "create_sheet/1 with valid data creates a sheet" do
      valid_attrs = %{purchases: []}

      assert {:ok, %Sheet{} = sheet} = Ledger.create_sheet(valid_attrs)
      assert sheet.purchases == []
    end

    test "create_sheet/1 with invalid data returns error changeset" do
      assert {:error, %Ecto.Changeset{}} = Ledger.create_sheet(@invalid_attrs)
    end

    test "update_sheet/2 with valid data updates the sheet" do
      sheet = sheet_fixture()
      update_attrs = %{purchases: []}

      assert {:ok, %Sheet{} = sheet} = Ledger.update_sheet(sheet, update_attrs)
      assert sheet.purchases == []
    end

    test "update_sheet/2 with invalid data returns error changeset" do
      sheet = sheet_fixture()
      assert {:error, %Ecto.Changeset{}} = Ledger.update_sheet(sheet, @invalid_attrs)
      assert sheet == Ledger.get_sheet!(sheet.id)
    end

    test "delete_sheet/1 deletes the sheet" do
      sheet = sheet_fixture()
      assert {:ok, %Sheet{}} = Ledger.delete_sheet(sheet)
      assert_raise Ecto.NoResultsError, fn -> Ledger.get_sheet!(sheet.id) end
    end

    test "change_sheet/1 returns a sheet changeset" do
      sheet = sheet_fixture()
      assert %Ecto.Changeset{} = Ledger.change_sheet(sheet)
    end
  end

  describe "purchases" do
    alias Chathams.Ledger.Purchase

    import Chathams.LedgerFixtures

    @invalid_attrs %{purchases: nil}

    test "list_purchases/0 returns all purchases" do
      purchase = purchase_fixture()
      assert Ledger.list_purchases() == [purchase]
    end

    test "get_purchase!/1 returns the purchase with given id" do
      purchase = purchase_fixture()
      assert Ledger.get_purchase!(purchase.id) == purchase
    end

    test "create_purchase/1 with valid data creates a purchase" do
      valid_attrs = %{purchases: []}

      assert {:ok, %Purchase{} = purchase} = Ledger.create_purchase(valid_attrs)
      assert purchase.purchases == []
    end

    test "create_purchase/1 with invalid data returns error changeset" do
      assert {:error, %Ecto.Changeset{}} = Ledger.create_purchase(@invalid_attrs)
    end

    test "update_purchase/2 with valid data updates the purchase" do
      purchase = purchase_fixture()
      update_attrs = %{purchases: []}

      assert {:ok, %Purchase{} = purchase} = Ledger.update_purchase(purchase, update_attrs)
      assert purchase.purchases == []
    end

    test "update_purchase/2 with invalid data returns error changeset" do
      purchase = purchase_fixture()
      assert {:error, %Ecto.Changeset{}} = Ledger.update_purchase(purchase, @invalid_attrs)
      assert purchase == Ledger.get_purchase!(purchase.id)
    end

    test "delete_purchase/1 deletes the purchase" do
      purchase = purchase_fixture()
      assert {:ok, %Purchase{}} = Ledger.delete_purchase(purchase)
      assert_raise Ecto.NoResultsError, fn -> Ledger.get_purchase!(purchase.id) end
    end

    test "change_purchase/1 returns a purchase changeset" do
      purchase = purchase_fixture()
      assert %Ecto.Changeset{} = Ledger.change_purchase(purchase)
    end
  end
end
