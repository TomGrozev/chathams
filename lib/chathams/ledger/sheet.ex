defmodule Chathams.Ledger.Sheet do
  use Ecto.Schema
  import Ecto.Changeset

  @derive {
    Blank.Schema,
    fields: [
      inserted_at: [
        label: "Created at"
      ],
      purchases: [
        display_field: :sid,
        searchable: false,
        sortable: false,
        # select: quote(do: dynamic([p], fragment("concat(?, ' ', ?)", p.first_name, p.last_name))),
        children: [
          sid: [],
          purchases: []
        ],
        readonly: true
      ]
    ],
    identity_field: :inserted_at,
    order_field: :inserted_at
  }

  schema "sheets" do
    has_many :purchases, Chathams.Ledger.Purchases

    timestamps(type: :utc_datetime)
  end

  @doc false
  @spec changeset(Sheet.t(), map()) :: Ecto.Changeset.t()
  def changeset(sheet, attrs) do
    sheet
    |> cast(attrs, [])
    |> cast_assoc(:purchases,
      sort_param: :purchases_sort,
      drop_param: :purchases_drop,
      required: true
    )
  end
end
