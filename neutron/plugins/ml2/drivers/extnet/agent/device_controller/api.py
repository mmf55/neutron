import abc

import six


@six.add_metaclass(abc.ABCMeta)
class ExtNetDeviceController(object):

    @abc.abstractmethod
    def create_segment(self, segment):
        pass

    @abc.abstractmethod
    def update_segment(self, id, segment):
        pass

    @abc.abstractmethod
    def delete_segment(self, id):
        pass

    @abc.abstractmethod
    def show_segment(self, id):
        pass


