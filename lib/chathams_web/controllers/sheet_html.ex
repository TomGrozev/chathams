defmodule ChathamsWeb.SheetHTML do
  use ChathamsWeb, :html

  embed_templates "sheet_html/*"

  # PROTOTYPE (issue #7): ArUco DICT_4X4_50 inner bits for ids 0-3, read from
  # OpenCV's `generateImageMarker`. "1" is a white cell. The marker adds a
  # one-cell black border around these bits.
  @aruco_bits %{
    0 => ~w(1011 0101 0011 0010),
    1 => ~w(0000 1111 1001 1010),
    2 => ~w(0011 0011 0010 1101),
    3 => ~w(1001 1001 0100 0110)
  }

  @doc """
  Corner marker: a 6x6-cell ArUco marker with a one-cell white quiet zone.
  The viewBox is 8 cells wide, so CSS sets the full size (marker plus quiet zone).
  """
  attr :id, :integer, required: true
  attr :class, :string, required: true

  def aruco_marker(assigns) do
    assigns = assign(assigns, :black_cells, black_cells(Map.fetch!(@aruco_bits, assigns.id)))

    ~H"""
    <svg
      class={["ls-marker", @class]}
      viewBox="-1 -1 8 8"
      shape-rendering="crispEdges"
      aria-hidden="true"
    >
      <rect x="-1" y="-1" width="8" height="8" fill="#fff" />
      <rect x="0" y="0" width="6" height="6" fill="#000" />
      <rect
        :for={{x, y} <- @black_cells}
        x={x}
        y={y}
        width="1"
        height="1"
        fill="#fff"
      />
    </svg>
    """
  end

  # The marker starts all black; white cells are painted over it.
  defp black_cells(rows) do
    for {row, y} <- Enum.with_index(rows, 1),
        {"1", x} <- row |> String.graphemes() |> Enum.with_index(1),
        do: {x, y}
  end

  @doc "The short instructions printed at the top of every page."
  def instructions(assigns) do
    ~H"""
    <ul class="ls-rules">
      <li>Write one amount in each box, for example 2.50.</li>
      <li>Bought some things together? Write the total in one box, for example 1.5.</li>
      <li>Not on the sheet, or your row is full? Use a blank row at the end.</li>
      <li>In a blank row, write your sid in capitals, one letter in each box.</li>
    </ul>
    """
  end

  @doc "Seven closed sid character cells for a blank row, with an example."
  attr :hint, :boolean, default: true

  def sid_cells(assigns) do
    ~H"""
    <div class="ls-sid">
      <div :for={_ <- 1..7} class="ls-box"></div>
    </div>
    <p :if={@hint} class="ls-sid-hint">Your sid in capitals, for example N G U Y E N A</p>
    """
  end
end
