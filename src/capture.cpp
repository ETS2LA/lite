#include "capture.h"

#include <optional>
#include <string>

#include <opencv2/opencv.hpp>

#include <d3d11_4.h>
#include <Windows.Graphics.Capture.Interop.h>
#include <Windows.Graphics.DirectX.Direct3D11.Interop.h>


using namespace std;
using namespace winrt::Windows::Graphics::Capture;
using namespace winrt::Windows::Graphics::DirectX;
using namespace winrt::Windows::Graphics::DirectX::Direct3D11;


WindowCapture::WindowCapture(
	optional<string> window_name,
	optional<uint8_t> display_index
):
window_name(window_name),
display_index(display_index) {}

void WindowCapture::initialize() {
	if (initialized_) {
		return;
	}


	D3D_FEATURE_LEVEL feature_levels[] = { D3D_FEATURE_LEVEL_11_1, D3D_FEATURE_LEVEL_11_0 };
    winrt::com_ptr<ID3D11Device> d3d_device;
    winrt::com_ptr<ID3D11DeviceContext> d3d_context;
    D3D_FEATURE_LEVEL created_level{};
    D3D11CreateDevice(
        nullptr, D3D_DRIVER_TYPE_HARDWARE, nullptr, D3D11_CREATE_DEVICE_BGRA_SUPPORT,
        feature_levels, _countof(feature_levels),
        D3D11_SDK_VERSION, d3d_device.put(), &created_level, d3d_context.put()
    );

    winrt::com_ptr<IDXGIDevice> dxgi_device;
    d3d_device.as(dxgi_device);

    winrt::com_ptr<IInspectable> inspectable_device;
    CreateDirect3D11DeviceFromDXGIDevice(
        dxgi_device.get(),
        inspectable_device.put()
    );
    d3d_device_ = inspectable_device.as<IDirect3DDevice>();


	auto interop_factory = winrt::get_activation_factory<GraphicsCaptureItem, IGraphicsCaptureItemInterop>();
	HMONITOR monitor_handle = MonitorFromWindow(nullptr, MONITOR_DEFAULTTOPRIMARY);
	interop_factory->CreateForMonitor(monitor_handle, winrt::guid_of<GraphicsCaptureItem>(), winrt::put_abi(item_));

	frame_pool_= Direct3D11CaptureFramePool::CreateFreeThreaded(
		d3d_device_,
		DirectXPixelFormat::B8G8R8A8UIntNormalized,
		2,
		item_.Size()
	);

	session_ = frame_pool_.CreateCaptureSession(
		item_
	);

	frame_pool_.FrameArrived(
		[this](winrt::Windows::Graphics::Capture::Direct3D11CaptureFramePool const &sender,
			   winrt::Windows::Foundation::IInspectable const &)
		{
			auto frame = sender.TryGetNextFrame();

			if (frame) {
				latest_frame_ = convert_frame_to_mat(frame);
			}
		}
	);

	initialized_ = true;
	session_.StartCapture();
}


cv::Mat* WindowCapture::convert_frame_to_mat(
	winrt::Windows::Graphics::Capture::Direct3D11CaptureFrame const& frame
) {
	auto surface = frame.Surface();
	auto access = surface.as<Windows::Graphics::DirectX::Direct3D11::IDirect3DDxgiInterfaceAccess>();
	winrt::com_ptr<ID3D11Texture2D> texture;
	access->GetInterface(IID_PPV_ARGS(texture.put()));

	winrt::com_ptr<ID3D11Device> device;
	texture->GetDevice(device.put());

	winrt::com_ptr<ID3D11DeviceContext> context;
	device->GetImmediateContext(context.put());

	D3D11_TEXTURE2D_DESC desc;
	texture->GetDesc(&desc);

	D3D11_TEXTURE2D_DESC staging_desc = desc;
	staging_desc.Usage = D3D11_USAGE_STAGING;
	staging_desc.BindFlags = 0;
	staging_desc.CPUAccessFlags = D3D11_CPU_ACCESS_READ;
	staging_desc.MiscFlags = 0;

	winrt::com_ptr<ID3D11Texture2D> stagingTexture;
	device->CreateTexture2D(&staging_desc, nullptr, stagingTexture.put());

	context->CopyResource(stagingTexture.get(), texture.get());

	D3D11_MAPPED_SUBRESOURCE mapped;
	context->Map(stagingTexture.get(), 0, D3D11_MAP_READ, 0, &mapped);

	if (latest_frame_ == nullptr) {
		latest_frame_ = new cv::Mat();
	}

	cv::Mat wrapper(desc.Height, desc.Width, CV_8UC4, mapped.pData, mapped.RowPitch);

	auto content_size = frame.ContentSize();
	if (content_size.Width != (int32_t)desc.Width || content_size.Height != (int32_t)desc.Height) {
		int w = content_size.Width < (int32_t)desc.Width ? content_size.Width : (int32_t)desc.Width;
		int h = content_size.Height < (int32_t)desc.Height ? content_size.Height : (int32_t)desc.Height;
		cv::Rect roi(0, 0, w, h);
		wrapper(roi).copyTo(*latest_frame_);
	} else {
		wrapper.copyTo(*latest_frame_);
	}

	context->Unmap(stagingTexture.get(), 0);

	return latest_frame_;
}


cv::Mat* WindowCapture::get_frame() {
	while (latest_frame_ == nullptr) {
		std::this_thread::sleep_for(std::chrono::milliseconds(1));
	}
	return latest_frame_;
}