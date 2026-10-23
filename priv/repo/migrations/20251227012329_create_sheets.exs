defmodule Chathams.Repo.Migrations.CreateSheets do
  use Ecto.Migration

  def change do
    create table(:sheets) do
      timestamps(type: :utc_datetime)
    end
  end
end
