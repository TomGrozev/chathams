defmodule Chathams.AccountsTest do
  use Chathams.DataCase

  alias Chathams.Accounts

  describe "staff" do
    alias Chathams.Accounts.Staff

    import Chathams.AccountsFixtures

    @invalid_attrs %{sid: nil, first_name: nil, last_name: nil}

    test "list_staff/0 returns all staff with the full name" do
      staff = staff_fixture()

      assert [listed] = Accounts.list_staff()
      assert listed.sid == staff.sid
      assert listed.full_name == "some first_name some last_name"
    end

    test "get_staff!/1 returns the staff with given sid" do
      staff = staff_fixture()
      assert Accounts.get_staff!(staff.sid) == staff
    end

    test "get_staff!/1 raises for a sid that is not a binary" do
      assert_raise ArgumentError, fn -> Accounts.get_staff!(123) end
    end

    test "create_staff/1 with valid data creates a staff" do
      valid_attrs = %{
        sid: "abc1234",
        first_name: "some first_name",
        last_name: "some last_name"
      }

      assert {:ok, %Staff{} = staff} = Accounts.create_staff(valid_attrs)
      assert staff.sid == "abc1234"
      assert staff.first_name == "some first_name"
      assert staff.last_name == "some last_name"
    end

    test "create_staff/1 does not cast balance" do
      attrs = %{
        sid: "abc1235",
        first_name: "some first_name",
        last_name: "some last_name",
        balance: 120.5
      }

      assert {:ok, %Staff{} = staff} = Accounts.create_staff(attrs)
      assert staff.balance == nil
    end

    test "create_staff/1 with invalid data returns error changeset" do
      assert {:error, %Ecto.Changeset{}} = Accounts.create_staff(@invalid_attrs)
    end

    test "update_staff/2 with valid data updates the staff" do
      staff = staff_fixture()

      update_attrs = %{
        first_name: "some updated first_name",
        last_name: "some updated last_name"
      }

      assert {:ok, %Staff{} = staff} = Accounts.update_staff(staff, update_attrs)
      assert staff.first_name == "some updated first_name"
      assert staff.last_name == "some updated last_name"
    end

    test "update_staff/2 with invalid data returns error changeset" do
      staff = staff_fixture()
      assert {:error, %Ecto.Changeset{}} = Accounts.update_staff(staff, @invalid_attrs)
      assert Accounts.get_staff!(staff.sid) == staff
    end

    test "delete_staff/1 deletes the staff" do
      staff = staff_fixture()
      assert {:ok, %Staff{}} = Accounts.delete_staff(staff)
      assert_raise Ecto.NoResultsError, fn -> Accounts.get_staff!(staff.sid) end
    end

    test "change_staff/1 returns a staff changeset" do
      staff = staff_fixture()
      assert %Ecto.Changeset{} = Accounts.change_staff(staff)
    end
  end
end
