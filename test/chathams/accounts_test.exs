defmodule Chathams.AccountsTest do
  use Chathams.DataCase

  alias Chathams.Accounts

  describe "staff" do
    alias Chathams.Accounts.Staff

    import Chathams.AccountsFixtures

    @invalid_attrs %{balance: nil, sid: nil, first_name: nil, last_name: nil}

    test "list_staff/0 returns all staff" do
      staff = staff_fixture()
      assert Accounts.list_staff() == [staff]
    end

    test "get_staff!/1 returns the staff with given id" do
      staff = staff_fixture()
      assert Accounts.get_staff!(staff.id) == staff
    end

    test "create_staff/1 with valid data creates a staff" do
      valid_attrs = %{balance: 120.5, sid: "some sid", first_name: "some first_name", last_name: "some last_name"}

      assert {:ok, %Staff{} = staff} = Accounts.create_staff(valid_attrs)
      assert staff.balance == 120.5
      assert staff.sid == "some sid"
      assert staff.first_name == "some first_name"
      assert staff.last_name == "some last_name"
    end

    test "create_staff/1 with invalid data returns error changeset" do
      assert {:error, %Ecto.Changeset{}} = Accounts.create_staff(@invalid_attrs)
    end

    test "update_staff/2 with valid data updates the staff" do
      staff = staff_fixture()
      update_attrs = %{balance: 456.7, sid: "some updated sid", first_name: "some updated first_name", last_name: "some updated last_name"}

      assert {:ok, %Staff{} = staff} = Accounts.update_staff(staff, update_attrs)
      assert staff.balance == 456.7
      assert staff.sid == "some updated sid"
      assert staff.first_name == "some updated first_name"
      assert staff.last_name == "some updated last_name"
    end

    test "update_staff/2 with invalid data returns error changeset" do
      staff = staff_fixture()
      assert {:error, %Ecto.Changeset{}} = Accounts.update_staff(staff, @invalid_attrs)
      assert staff == Accounts.get_staff!(staff.id)
    end

    test "delete_staff/1 deletes the staff" do
      staff = staff_fixture()
      assert {:ok, %Staff{}} = Accounts.delete_staff(staff)
      assert_raise Ecto.NoResultsError, fn -> Accounts.get_staff!(staff.id) end
    end

    test "change_staff/1 returns a staff changeset" do
      staff = staff_fixture()
      assert %Ecto.Changeset{} = Accounts.change_staff(staff)
    end
  end
end
