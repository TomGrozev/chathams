defmodule Chathams.Accounts do
  @moduledoc """
  The Accounts context.
  """

  import Ecto.Query, warn: false
  alias Chathams.Repo

  alias Chathams.Accounts.Staff

  @doc """
  Returns the list of staff.

  ## Examples

      iex> list_staff()
      [%Staff{}, ...]

  """
  @spec list_staff() :: [Staff.t()]
  def list_staff do
    Repo.all(
      from(s in Staff,
        select: %{s | full_name: fragment("concat(?, ' ', ?)", s.first_name, s.last_name)}
      )
    )
  end

  @doc """
  Gets a single staff.

  Raises `Ecto.NoResultsError` if the Staff does not exist.

  ## Examples

      iex> get_staff!("abcdef")
      %Staff{}

      iex> get_staff!("none")
      ** (Ecto.NoResultsError)

  """
  @spec get_staff!(String.t()) :: Staff.t()
  def get_staff!(sid) when is_binary(sid), do: Repo.get!(Staff, sid)

  def get_staff!(_), do: raise(ArgumentError, message: "invalid sid supplied.")

  @doc """
  Creates a staff.

  ## Examples

      iex> create_staff(%{field: value})
      {:ok, %Staff{}}

      iex> create_staff(%{field: bad_value})
      {:error, %Ecto.Changeset{}}

  """
  @spec create_staff(map()) :: {:ok, Staff.t()} | {:error, Ecto.Changeset.t()}
  def create_staff(attrs) do
    %Staff{}
    |> Staff.changeset(attrs)
    |> Repo.insert()
  end

  @doc """
  Updates a staff.

  ## Examples

      iex> update_staff(staff, %{field: new_value})
      {:ok, %Staff{}}

      iex> update_staff(staff, %{field: bad_value})
      {:error, %Ecto.Changeset{}}

  """
  @spec update_staff(Staff.t(), map()) :: {:ok, Staff.t()} | {:error, Ecto.Changeset.t()}
  def update_staff(%Staff{} = staff, attrs) do
    staff
    |> Staff.changeset(attrs)
    |> Repo.update()
  end

  @doc """
  Deletes a staff.

  ## Examples

      iex> delete_staff(staff)
      {:ok, %Staff{}}

      iex> delete_staff(staff)
      {:error, %Ecto.Changeset{}}

  """
  @spec delete_staff(Staff.t()) :: {:ok, Staff.t()} | {:error, Ecto.Changeset.t()}
  def delete_staff(%Staff{} = staff) do
    Repo.delete(staff)
  end

  @doc """
  Returns an `%Ecto.Changeset{}` for tracking staff changes.

  ## Examples

      iex> change_staff(staff)
      %Ecto.Changeset{data: %Staff{}}

  """
  @spec change_staff(Staff.t(), map()) :: Ecto.Changeset.t()
  def change_staff(%Staff{} = staff, attrs \\ %{}) do
    Staff.changeset(staff, attrs)
  end
end
