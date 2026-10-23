defmodule Chathams.Ledger do
  @moduledoc """
  The Ledger context.
  """

  import Ecto.Query, warn: false
  alias Chathams.Repo

  alias Chathams.Ledger.Sheet

  @doc """
  Returns the list of sheets.

  ## Examples

      iex> list_sheets()
      [%Sheet{}, ...]

  """
  @spec list_sheets() :: [Sheet.t()]
  def list_sheets do
    Repo.all(Sheet)
  end

  @doc """
  Gets a single sheet.

  Raises `Ecto.NoResultsError` if the Sheet does not exist.

  ## Examples

      iex> get_sheet!(123)
      %Sheet{}

      iex> get_sheet!(456)
      ** (Ecto.NoResultsError)

  """
  @spec get_sheet!(integer()) :: Sheet.t()
  def get_sheet!(id), do: Repo.get!(Sheet, id)

  @doc """
  Creates a sheet.

  ## Examples

      iex> create_sheet(%{field: value})
      {:ok, %Sheet{}}

      iex> create_sheet(%{field: bad_value})
      {:error, %Ecto.Changeset{}}

  """
  @spec create_sheet(map()) :: {:ok, Sheet.t()} | {:error, Ecto.Changeset.t()}
  def create_sheet(attrs) do
    %Sheet{}
    |> Sheet.changeset(attrs)
    |> Repo.insert()
  end

  @doc """
  Updates a sheet.

  ## Examples

      iex> update_sheet(sheet, %{field: new_value})
      {:ok, %Sheet{}}

      iex> update_sheet(sheet, %{field: bad_value})
      {:error, %Ecto.Changeset{}}

  """
  @spec update_sheet(Sheet.t(), map()) :: {:ok, Sheet.t()} | {:error, Ecto.Changeset.t()}
  def update_sheet(%Sheet{} = sheet, attrs) do
    sheet
    |> Sheet.changeset(attrs)
    |> Repo.update()
  end

  @doc """
  Deletes a sheet.

  ## Examples

      iex> delete_sheet(sheet)
      {:ok, %Sheet{}}

      iex> delete_sheet(sheet)
      {:error, %Ecto.Changeset{}}

  """
  @spec delete_sheet(Sheet.t()) :: {:ok, Sheet.t()} | {:error, Ecto.Changeset.t()}
  def delete_sheet(%Sheet{} = sheet) do
    Repo.delete(sheet)
  end

  @doc """
  Returns an `%Ecto.Changeset{}` for tracking sheet changes.

  ## Examples

      iex> change_sheet(sheet)
      %Ecto.Changeset{data: %Sheet{}}

  """
  @spec change_sheet(Sheet.t(), map()) :: Ecto.Changeset.t()
  def change_sheet(%Sheet{} = sheet, attrs \\ %{}) do
    Sheet.changeset(sheet, attrs)
  end

  alias Chathams.Ledger.Purchases

  @doc """
  Returns the list of purchases.

  ## Examples

      iex> list_purchases()
      [%Purchases{}, ...]

  """
  @spec list_purchases() :: [Purchases.t()]
  def list_purchases do
    Repo.all(Purchases)
  end

  @doc """
  Gets a single sheet's purchases.

  Raises `Ecto.NoResultsError` if the Purchases don't exist.

  ## Examples

      iex> get_purchases!(123)
      %Purchases{}

      iex> get_purchases!(456)
      ** (Ecto.NoResultsError)

  """
  @spec get_purchases!(integer()) :: Purchases.t()
  def get_purchases!(id), do: Repo.get!(Purchases, id)

  @doc """
  Returns an `%Ecto.Changeset{}` for tracking changes to purchases.

  ## Examples

      iex> change_purchases(purchase)
      %Ecto.Changeset{data: %Purchases{}}

  """
  @spec change_purchase(Purchases.t(), map()) :: Ecto.Changeset.t()
  def change_purchase(%Purchases{} = purchases, attrs \\ %{}) do
    Purchases.changeset(purchases, attrs)
  end
end
