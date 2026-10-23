defmodule Chathams.Repo.Migrations.CreatePurchases do
  use Ecto.Migration

  def change do
    create table(:purchases) do
      add :purchases, {:array, :float}
      add :sheet_id, references(:sheets, on_delete: :nothing)
      add :sid, references(:staff, on_delete: :nothing, column: :sid, type: :string)

      timestamps(type: :utc_datetime)
    end

    create index(:purchases, [:sheet_id])
    create index(:purchases, [:sid])
  end
end
