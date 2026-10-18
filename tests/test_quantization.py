"""Image quality regressions at a fixed palette budget, not just file validity."""

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from pixel_coloring.importer.image_importer import convert_image
from pixel_coloring.importer.quantization import oklab_to_rgb, quantize_image, rgb_to_oklab


def accent_image(width=320, height=180):
    y, x = np.mgrid[:height, :width]
    pixels = np.stack((50 + x * .5, 85 + x * .35 + y * .15,
                       130 + x * .25 + y * .2), axis=-1).clip(0, 255).astype(np.uint8)
    pixels[80:84, 140:144] = [245, 30, 180]
    return Image.fromarray(pixels)


def perceptual_error(original, result):
    return ((rgb_to_oklab(original) - rgb_to_oklab(result)) ** 2).sum(axis=-1).mean()


def test_small_accent_survives_without_increasing_sixty_color_budget():
    source = accent_image()
    before = np.asarray(source.quantize(60, method=Image.Quantize.MEDIANCUT).convert('RGB'))
    palette, target = quantize_image(source, 60)
    after = palette[target]
    accent = np.array([245, 30, 180])
    assert np.linalg.norm(before[80, 140].astype(float) - accent) > 100
    assert np.linalg.norm(after[80, 140].astype(float) - accent) < 3
    assert len(palette) <= 60
    assert perceptual_error(np.asarray(source), after) < perceptual_error(np.asarray(source), before)


@pytest.mark.parametrize('count', [1, 2, 15, 60, 256])
def test_existing_colors_are_lossless_when_they_fit_budget(count):
    rng = np.random.default_rng(count)
    colors = np.unique(rng.integers(0, 256, (count * 2, 3), dtype=np.uint8), axis=0)[:count]
    pixels = np.tile(colors, (17, 3, 1))
    source = Image.fromarray(pixels)
    palette, target = quantize_image(source, max(2, count))
    assert np.array_equal(palette[target], pixels)
    assert len(palette) == count


@pytest.mark.parametrize('budget', [2, 16, 60, 250, 256])
def test_deterministic_results_respect_requested_palette_budget(budget):
    rng = np.random.default_rng(8)
    pixels = rng.integers(0, 256, (23, 37, 3), dtype=np.uint8)
    image = Image.fromarray(pixels)
    palette, target = quantize_image(image, budget)
    again_palette, again_target = quantize_image(image, budget)
    assert 1 <= len(palette) <= budget
    assert target.shape == pixels.shape[:2]
    assert np.array_equal(palette, again_palette)
    assert np.array_equal(target, again_target)
    assert len(np.unique(palette, axis=0)) == len(palette)
    assert set(np.unique(target)) == set(range(len(palette)))
    assert not np.any(pixels != np.asarray(image))


def test_near_monochrome_does_not_collapse_to_thirty_two_histogram_bins():
    values = np.arange(256, dtype=np.uint8)
    pixels = np.tile(values[None, :, None], (16, 1, 3))
    palette, target = quantize_image(Image.fromarray(pixels), 60)
    assert len(palette) >= 55
    assert np.max(np.abs(palette[target].astype(float) - pixels)) <= 5
    # Neutral inputs stay neutral; no green or magenta tint in the result.
    assert np.max(np.ptp(palette.astype(int), axis=1)) <= 1


def test_no_dither_identical_colors_always_receive_same_palette_entry():
    source = np.asarray(accent_image())
    # Reverse a copy so neighboring pixels and scan direction differ.
    mirrored = np.concatenate((source, source[:, ::-1]), axis=1)
    palette, target = quantize_image(Image.fromarray(mirrored), 16)
    assert np.array_equal(target[:, :320], target[:, 320:][:, ::-1])
    assert len(palette) <= 16


def test_srgb_oklab_reference_colors_and_round_trip():
    colors = np.array([[255, 0, 0], [0, 255, 0], [0, 0, 255], [0, 0, 0], [255, 255, 255]])
    lab = rgb_to_oklab(colors)
    assert lab[0] == pytest.approx([.627955, .224863, .125846], abs=1e-5)
    assert lab[1] == pytest.approx([.866440, -.233888, .179498], abs=1e-5)
    assert lab[2] == pytest.approx([.452014, -.032457, -.311528], abs=1e-5)
    assert np.array_equal(oklab_to_rgb(lab), colors)
    rng = np.random.default_rng(37)
    colors = rng.integers(0, 256, (8192, 3), dtype=np.uint8)
    assert np.array_equal(oklab_to_rgb(rgb_to_oklab(colors)), colors)


def test_real_artwork_error_decreases_at_same_sixty_colors():
    path = Path(__file__).resolve().parents[1] / 'packaging/sources/harikalar/018-statue-of-liberty.png'
    if not path.exists():
        pytest.skip('Original artwork is absent from this source distribution')
    with Image.open(path) as source:
        image = source.convert('RGB')
    image.thumbnail((720, 540), Image.Resampling.LANCZOS)
    original = np.asarray(image)
    baseline = np.asarray(image.quantize(60, method=Image.Quantize.MEDIANCUT).convert('RGB'))
    painting = convert_image(image, 'Quality comparison', colors=60)
    converted = painting.palette[painting.target_map]
    assert len(painting.palette) <= 60
    assert perceptual_error(original, converted) < perceptual_error(original, baseline) * .7


def test_full_hd_keeps_dimensions_and_accent_with_sixty_colors():
    # An actual 1920x1080 input, rather than testing only thumbnail conversion.
    image = accent_image().resize((1920, 1080), Image.Resampling.NEAREST)
    painting = convert_image(image, 'Full HD', colors=60)
    assert (painting.width, painting.height) == (1920, 1080)
    assert len(painting.palette) <= 60
    assert np.linalg.norm(painting.palette[painting.target_map[480, 840]].astype(float) - [245, 30, 180]) < 3
