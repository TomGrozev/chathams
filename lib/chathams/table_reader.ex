defmodule Chathams.TableReader do
  def process(path) do
    # tmp_dir = System.tmp_dir!() |> Path.join("/")
    with {:ok, doc} <- PDFium.load_document(path),
         {:ok, images} <- pdf_to_images(doc),
         :ok <- PDFium.close_document(doc) do
      Enum.map(images, &process_page/1)
    end
    |> dbg()
  end

  defp pdf_to_images(doc) do
    with {:ok, pages} <- PDFium.get_page_count(doc) do
      Enum.reduce_while(0..(pages - 1), {:ok, []}, fn page, {:ok, acc} ->
        case page_to_image(doc, page) do
          {:ok, img} -> {:cont, {:ok, [img | acc]}}
          {:error, reason} -> {:halt, {:error, reason}}
        end
      end)
    end
  end

  defp page_to_image(doc, page) do
    with {:ok, binary, w, h} <- PDFium.get_page_bitmap(doc, page, 300) do
      Vix.Vips.Image.new_from_binary(binary, w, h, 4, :VIPS_FORMAT_UCHAR)
    end
  end

  defp process_page(img) do
    [r, g, b, _mask] = Image.split_bands(img)
    {:ok, img} = Image.join_bands([r, g, b])

    with {:ok, e_img} <- Image.to_evision(img),
         {:ok, greyscale} <- Evision.cvtColor(e_img, Evision.Constant.cv_IMREAD_GRAYSCALE()),
         {:ok, threshold} <-
           Evision.threshold(
             greyscale,
             0,
             255,
             Evision.ThresholdTypes.cv_THRESH_BINARY() + Evision.ThresholdTypes.cv_THRESH_OTSU()
           ),
         {:ok, inverted} <- Evision.Mat.bitwise_not(threshold),
         {:ok, dilated} <- Evision.dilate(inverted, None, iterations: 5) do
    end
  end
end
