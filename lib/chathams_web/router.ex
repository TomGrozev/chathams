defmodule ChathamsWeb.Router do
  use ChathamsWeb, :router

  import Blank.Router

  pipeline :browser do
    plug :accepts, ["html"]
    plug :fetch_session
    plug :fetch_live_flash
    plug :put_root_layout, html: {ChathamsWeb.Layouts, :root}
    plug :protect_from_forgery
    plug :put_secure_browser_headers
  end

  pipeline :api do
    plug :accepts, ["json"]
  end

  scope "/", ChathamsWeb do
    pipe_through :browser

    get "/", PageController, :home

    live "/staff", StaffLive.Index, :index
    live "/staff/new", StaffLive.Form, :new
    live "/staff/:id", StaffLive.Show, :show
    live "/staff/:id/edit", StaffLive.Form, :edit
  end

  blank_admin "/admin" do
    admin_page("/staff", ChathamsWeb.Admin.StaffLive)
    admin_page("/sheets", ChathamsWeb.Admin.SheetsLive)

    get "/sheets/sheet/blank", ChathamsWeb.SheetController, :blank
  end

  # Other scopes may use custom stacks.
  # scope "/api", ChathamsWeb do
  #   pipe_through :api
  # end

  # Enable LiveDashboard and Swoosh mailbox preview in development
  if Application.compile_env(:chathams, :dev_routes) do
    # If you want to use the LiveDashboard in production, you should put
    # it behind authentication and allow only admins to access it.
    # If your application does not have an admins-only section yet,
    # you can use Plug.BasicAuth to set up some basic authentication
    # as long as you are also using SSL (which you should anyway).
    import Phoenix.LiveDashboard.Router

    scope "/dev" do
      pipe_through :browser

      live_dashboard "/dashboard", metrics: ChathamsWeb.Telemetry
      forward "/mailbox", Plug.Swoosh.MailboxPreview
    end
  end
end
