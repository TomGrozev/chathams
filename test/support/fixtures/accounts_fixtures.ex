defmodule Chathams.AccountsFixtures do
  @moduledoc """
  This module defines test helpers for creating
  entities via the `Chathams.Accounts` context.
  """

  @doc """
  Generate a unique staff sid.
  """
  def unique_staff_sid, do: "some sid#{System.unique_integer([:positive])}"

  @doc """
  Generate a staff.
  """
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
