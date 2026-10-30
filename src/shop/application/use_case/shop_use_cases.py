from dataclasses import dataclass

from shop.application.port.inbound.follow_product_port import FollowProductPort
from shop.application.port.inbound.get_product_image_port import GetProductImagePort
from shop.application.port.inbound.get_product_port import GetProductPort
from shop.application.port.inbound.place_order_port import PlaceOrderPort
from shop.application.port.inbound.render_label_port import RenderLabelPort
from shop.application.port.inbound.save_note_port import SaveNotePort
from shop.application.port.inbound.store_file_port import StoreFilePort
from shop.application.port.inbound.track_order_port import TrackOrderPort


@dataclass(frozen=True, slots=True)
class ShopUseCases:
    get_product: GetProductPort
    place_order: PlaceOrderPort
    follow_product: FollowProductPort
    track_order: TrackOrderPort
    get_product_image: GetProductImagePort
    store_file: StoreFilePort
    render_label: RenderLabelPort
    save_note: SaveNotePort
