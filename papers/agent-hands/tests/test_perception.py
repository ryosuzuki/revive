import io,json,unittest
from PIL import Image
from agent_hands.backend import Backend

class PerceptionTests(unittest.TestCase):
 def test_normalized_boxes_are_scaled_and_bad_regions_removed(self):
  stream=io.BytesIO();Image.new('RGB',(1280,720)).save(stream,format='JPEG')
  backend=Backend();backend.generate=lambda *args:{'text':json.dumps({'objects':[{'bbox':[100,200,500,800],'parts':{'lid':'T:center:center','invalid':'center'}}]})}
  result=backend.detect(stream.getvalue(),'Describe this object')
  self.assertEqual(result['objects'][0]['bbox'],[128,144,640,576])
  self.assertEqual(result['objects'][0]['parts'],{'lid':'T:center:center'})
