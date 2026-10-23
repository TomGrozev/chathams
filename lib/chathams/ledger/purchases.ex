defmodule Chathams.Ledger.Purchases do
  use Ecto.Schema
  import Ecto.Changeset

  schema "purchases" do
    field :purchases, {:array, :float}

    belongs_to :sheet, Chathams.Ledger.Sheet
    belongs_to :staff, Chathams.Accounts.Staff, foreign_key: :sid, references: :sid, type: :string

    timestamps(type: :utc_datetime)
  end

  @doc false
  def changeset(purchase, attrs) do
    purchase
    |> cast(attrs, [:purchases])
    |> validate_required([:purchases])
  end
end
