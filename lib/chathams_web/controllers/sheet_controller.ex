defmodule ChathamsWeb.SheetController do
  # PROTOTYPE (issue #7, "What does the new ledger sheet template look like?").
  # Three ledger sheet variants on the existing blank sheet route, switched by
  # `?variant=A|B|C`. Staff are fake and generated here, so no real name can
  # reach a printout. Throwaway: lives on branch prototype/ledger-sheet-template.
  @moduledoc false
  use ChathamsWeb, :controller

  @blank_row_pages 3

  @variants %{
    "A" => %{name: "Dense portrait", rows: 10},
    "B" => %{name: "Landscape wide", rows: 8},
    "B2" => %{name: "Landscape wide, refined", rows: 8},
    "C" => %{name: "Staff blocks", rows: 6}
  }

  # Clearly fake staff. Each sid follows the sid rule: seven characters,
  # letters first, optional trailing digits.
  @fake_staff [
    {"Alex Example", "EXAMPLA"},
    {"Bea Sample", "SAMPLEB"},
    {"Cal Dummy", "DUMMYC1"},
    {"Dee Fictional", "FICTIOD"},
    {"Eli Placeholder", "PLACEHE"},
    {"Fay Mockup", "MOCKUPF"},
    {"Gus Specimen", "SPECIMG"},
    {"Hal Prototype", "PROTOTH"},
    {"Ivy Testcase", "TESTCAI"},
    {"Jo Fixture", "FIXTURJ"},
    {"Kit Stub", "STUBK12"},
    {"Lou Pretend", "PRETENL"},
    {"Max Madeup", "MADEUPM"},
    {"Nia Notreal", "NOTREAN"},
    {"Oz Imaginary", "IMAGINO"},
    {"Pam Lorem", "LOREMP1"},
    {"Quinn Ipsum", "IPSUMQ1"},
    {"Ray Mockface", "MOCKFAR"},
    {"Sam Dryrun", "DRYRUNS"},
    {"Tia Pseudo", "PSEUDOT"},
    {"Uma Ersatz", "ERSATZU"},
    {"Vic Facsimile", "FACSIMV"},
    {"Wren Sampleton", "SAMPLEW"},
    {"Xan Draftly", "DRAFTLX"},
    {"Yui Testwell", "TESTWEY"},
    {"Zed Nobody", "NOBODYZ"}
  ]

  @spec blank(Plug.Conn.t(), map()) :: Plug.Conn.t()
  def blank(conn, params) do
    key = variant_key(params)
    variant = Map.fetch!(@variants, key)

    staff = Enum.map(@fake_staff, fn {name, sid} -> %{full_name: name, sid: sid, qr: qr(sid)} end)

    keys = @variants |> Map.keys() |> Enum.sort()
    index = Enum.find_index(keys, &(&1 == key))

    conn
    |> assign(:variant, key)
    |> assign(:variant_name, variant.name)
    |> assign(:prev_variant, Enum.at(keys, index - 1))
    |> assign(:next_variant, Enum.at(keys, rem(index + 1, length(keys))))
    |> assign(:pages, pages(staff, variant.rows))
    |> assign(:show_switcher, Application.get_env(:chathams, :dev_routes, false))
    |> render(:blank)
  end

  defp variant_key(%{"variant" => key}) when is_map_key(@variants, key), do: key
  defp variant_key(_params), do: "A"

  # Every page of a variant has the same row count, so the last staff page is
  # filled with blank rows and blank sheets follow.
  defp pages(staff, rows) do
    staff_pages =
      staff
      |> Enum.chunk_every(rows, rows, Stream.repeatedly(fn -> :blank end))

    staff_pages ++ List.duplicate(List.duplicate(:blank, rows), @blank_row_pages)
  end

  defp qr(sid) do
    sid
    |> EQRCode.encode(:m)
    |> EQRCode.svg(viewbox: true, background_color: "#ffffff", color: "#000000")
    |> Phoenix.HTML.raw()
  end
end
