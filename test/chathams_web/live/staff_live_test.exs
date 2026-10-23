defmodule ChathamsWeb.StaffLiveTest do
  use ChathamsWeb.ConnCase

  import Phoenix.LiveViewTest
  import Chathams.AccountsFixtures

  @create_attrs %{balance: 120.5, sid: "some sid", first_name: "some first_name", last_name: "some last_name"}
  @update_attrs %{balance: 456.7, sid: "some updated sid", first_name: "some updated first_name", last_name: "some updated last_name"}
  @invalid_attrs %{balance: nil, sid: nil, first_name: nil, last_name: nil}
  defp create_staff(_) do
    staff = staff_fixture()

    %{staff: staff}
  end

  describe "Index" do
    setup [:create_staff]

    test "lists all staff", %{conn: conn, staff: staff} do
      {:ok, _index_live, html} = live(conn, ~p"/staff")

      assert html =~ "Listing Staff"
      assert html =~ staff.sid
    end

    test "saves new staff", %{conn: conn} do
      {:ok, index_live, _html} = live(conn, ~p"/staff")

      assert {:ok, form_live, _} =
               index_live
               |> element("a", "New Staff")
               |> render_click()
               |> follow_redirect(conn, ~p"/staff/new")

      assert render(form_live) =~ "New Staff"

      assert form_live
             |> form("#staff-form", staff: @invalid_attrs)
             |> render_change() =~ "can&#39;t be blank"

      assert {:ok, index_live, _html} =
               form_live
               |> form("#staff-form", staff: @create_attrs)
               |> render_submit()
               |> follow_redirect(conn, ~p"/staff")

      html = render(index_live)
      assert html =~ "Staff created successfully"
      assert html =~ "some sid"
    end

    test "updates staff in listing", %{conn: conn, staff: staff} do
      {:ok, index_live, _html} = live(conn, ~p"/staff")

      assert {:ok, form_live, _html} =
               index_live
               |> element("#staff_collection-#{staff.id} a", "Edit")
               |> render_click()
               |> follow_redirect(conn, ~p"/staff/#{staff}/edit")

      assert render(form_live) =~ "Edit Staff"

      assert form_live
             |> form("#staff-form", staff: @invalid_attrs)
             |> render_change() =~ "can&#39;t be blank"

      assert {:ok, index_live, _html} =
               form_live
               |> form("#staff-form", staff: @update_attrs)
               |> render_submit()
               |> follow_redirect(conn, ~p"/staff")

      html = render(index_live)
      assert html =~ "Staff updated successfully"
      assert html =~ "some updated sid"
    end

    test "deletes staff in listing", %{conn: conn, staff: staff} do
      {:ok, index_live, _html} = live(conn, ~p"/staff")

      assert index_live |> element("#staff_collection-#{staff.id} a", "Delete") |> render_click()
      refute has_element?(index_live, "#staff-#{staff.id}")
    end
  end

  describe "Show" do
    setup [:create_staff]

    test "displays staff", %{conn: conn, staff: staff} do
      {:ok, _show_live, html} = live(conn, ~p"/staff/#{staff}")

      assert html =~ "Show Staff"
      assert html =~ staff.sid
    end

    test "updates staff and returns to show", %{conn: conn, staff: staff} do
      {:ok, show_live, _html} = live(conn, ~p"/staff/#{staff}")

      assert {:ok, form_live, _} =
               show_live
               |> element("a", "Edit")
               |> render_click()
               |> follow_redirect(conn, ~p"/staff/#{staff}/edit?return_to=show")

      assert render(form_live) =~ "Edit Staff"

      assert form_live
             |> form("#staff-form", staff: @invalid_attrs)
             |> render_change() =~ "can&#39;t be blank"

      assert {:ok, show_live, _html} =
               form_live
               |> form("#staff-form", staff: @update_attrs)
               |> render_submit()
               |> follow_redirect(conn, ~p"/staff/#{staff}")

      html = render(show_live)
      assert html =~ "Staff updated successfully"
      assert html =~ "some updated sid"
    end
  end
end
