defmodule Chathams.Repo.Migrations.CreateStaff do
  use Ecto.Migration

  def change do
    create table(:staff, primary_key: false) do
      add :sid, :string, size: 7, primary_key: true
      add :first_name, :string
      add :last_name, :string
      add :balance, :float

      timestamps(type: :utc_datetime)
    end
  end
end
