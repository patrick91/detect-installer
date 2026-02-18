class DetectInstallerTest < Formula
  include Language::Python::Virtualenv

  desc "Companion CLI for testing detect-installer"
  homepage "https://github.com/patrick91/detect-installer"
  # TODO: update url and sha256 when published to PyPI
  url "https://files.pythonhosted.org/packages/source/d/detect-installer-test/detect_installer_test-0.1.0.tar.gz"
  sha256 "PLACEHOLDER"
  license "0BSD"

  depends_on "python@3.12"

  resource "detect-installer" do
    # TODO: update url and sha256 when published to PyPI
    url "https://files.pythonhosted.org/packages/source/d/detect-installer/detect_installer-0.1.0.tar.gz"
    sha256 "PLACEHOLDER"
  end

  def install
    virtualenv_install_with_resources
  end

  test do
    output = shell_output("#{bin}/detect-installer-test")
    data = JSON.parse(output)
    assert_equal "brew", data["installer"]
  end
end
