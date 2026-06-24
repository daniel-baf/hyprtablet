pkgname=hyprtablet
pkgver=0.1.0
pkgrel=1
pkgdesc='Native GTK utility for mapping graphics tablets to monitors on Hyprland'
arch=('any')
url='https://github.com/daniel-baf/hyprtablet'
license=('MIT')
depends=('gtk4' 'libadwaita' 'python' 'python-gobject' 'hyprland')
makedepends=('python-build' 'python-installer' 'python-wheel' 'python-setuptools')
source=("$pkgname-$pkgver.tar.gz::$url/archive/refs/tags/v$pkgver.tar.gz")
sha256sums=('SKIP')

build() {
  cd "$pkgname-$pkgver"
  python -m build --wheel --no-isolation
}

package() {
  cd "$pkgname-$pkgver"
  python -m installer --destdir="$pkgdir" dist/*.whl
  install -Dm644 dev.hyprtablet.Hyprtablet.desktop "$pkgdir/usr/share/applications/dev.hyprtablet.Hyprtablet.desktop"
  install -Dm644 LICENSE "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
}
