defmodule Chathams.AccountsFixtures do
  @moduledoc """
  This module defines test helpers for creating
  entities via the `Chathams.Accounts` context.
  """

  @doc """
  Generate a unique staff sid.
  """
  @spec unique_staff_sid() :: String.t()
  def unique_staff_sid do
    suffix =
      "0000"
      |> Kernel.<>(Integer.to_string(System.unique_integer([:positive])))
      |> String.slice(-4, 4)

    "tst" <> suffix
  end

  @doc """
  Generate a staff.
  """
  @spec staff_fixture(map()) :: Chathams.Accounts.Staff.t()
  def staff_fixture(attrs \\ %{}) do
    {:ok, staff} =
      attrs
      |> Enum.into(%{
        balance: 120.5,
        first_name: "some first_name",
        last_name: "some last_name",
        sid: unique_staff_sid()
      })
      |> Chathams.Accounts.create_staff()

    staff
  end
end
