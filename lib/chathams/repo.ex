defmodule Chathams.Repo do
  use Ecto.Repo,
    otp_app: :chathams,
    adapter: Ecto.Adapters.Postgres
end
