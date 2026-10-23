defmodule Chathams.Accounts.Staff do
  use Ecto.Schema
  import Ecto.Changeset
  import Ecto.Query

  @derive {
    Blank.Schema,
    fields: [
      sid: [searchable: true],
      full_name: [
        select: quote(do: dynamic([s], fragment("concat(?, ' ', ?)", s.first_name, s.last_name))),
        readonly: true
      ],
      balance: [
        module: Blank.Fields.Currency
      ],
      purchases: [
        readonly: false
      ]
    ],
    identity_field: :sid,
    order_field: :inserted_at
  }

  @primary_key {:sid, :string, []}
  schema "staff" do
    field :first_name, :string
    field :last_name, :string
    field :full_name, :string, virtual: true
    field :balance, :float

    has_many :purchases, Chathams.Ledger.Purchases, foreign_key: :sid

    timestamps(type: :utc_datetime)
  end

  @doc false
  @spec changeset(Staff.t(), map()) :: Ecto.Changeset.t()
  def changeset(staff, attrs) do
    staff
    |> cast(attrs, [:sid, :first_name, :last_name])
    |> validate_required([:sid, :first_name, :last_name])
    |> unique_constraint(:sid)
  end
end
