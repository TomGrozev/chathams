defmodule Chathams.Application do
  # See https://hexdocs.pm/elixir/Application.html
  # for more information on OTP Applications
  @moduledoc false

  use Application

  @impl true
  def start(_type, _args) do
    children = [
      ChathamsWeb.Telemetry,
      Chathams.Repo,
      {DNSCluster, query: Application.get_env(:chathams, :dns_cluster_query) || :ignore},
      {Phoenix.PubSub, name: Chathams.PubSub},
      # Start a worker by calling: Chathams.Worker.start_link(arg)
      # {Chathams.Worker, arg},
      # Start to serve requests, typically the last entry
      ChathamsWeb.Endpoint
    ]

    # See https://hexdocs.pm/elixir/Supervisor.html
    # for other strategies and supported options
    opts = [strategy: :one_for_one, name: Chathams.Supervisor]
    Supervisor.start_link(children, opts)
  end

  # Tell Phoenix to update the endpoint configuration
  # whenever the application is updated.
  @impl true
  def config_change(changed, _new, removed) do
    ChathamsWeb.Endpoint.config_change(changed, removed)
    :ok
  end
end
