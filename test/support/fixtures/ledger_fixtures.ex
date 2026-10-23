defmodule Chathams.LedgerFixtures do
  @moduledoc """
  This module defines test helpers for creating
  entities via the `Chathams.Ledger` context.
  """

  @doc """
  Generate a sheet.
  """
  def sheet_fixture(attrs \\ %{}) do
    {:ok, sheet} =
      attrs
      |> Enum.into(%{
        purchases: []
      })
      |> Chathams.Ledger.create_sheet()

    sheet
  end

  @doc """
  Generate a purchase.
  """
  def purchase_fixture(attrs \\ %{}) do
    {:ok, purchase} =
      attrs
      |> Enum.into(%{
        purchases: []
      })
      |> Chathams.Ledger.create_purchase()

    purchase
  end
end
