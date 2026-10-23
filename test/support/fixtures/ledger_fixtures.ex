defmodule Chathams.LedgerFixtures do
  @moduledoc """
  This module defines test helpers for creating
  entities via the `Chathams.Ledger` context.
  """

  @doc """
  Generate a sheet with one purchase row.
  """
  @spec sheet_fixture(map()) :: Chathams.Ledger.Sheet.t()
  def sheet_fixture(attrs \\ %{}) do
    {:ok, sheet} =
      attrs
      |> Enum.into(%{
        purchases: [%{purchases: [1.0]}]
      })
      |> Chathams.Ledger.create_sheet()

    sheet
  end
end
