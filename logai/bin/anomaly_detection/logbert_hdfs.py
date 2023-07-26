import os

from logai.algorithms.factory import AlgorithmFactory
from logai.algorithms.nn_model.logbert.configs import LogBERTConfig
from logai.algorithms.vectorization_algo.logbert import LogBERTVectorizerParams
from logai.applications.openset.anomaly_detection.openset_anomaly_detection_workflow import OpenSetADWorkflowConfig, validate_config_dict
from logai.utils.file_utils import read_file
from logai.utils.dataset_utils import split_train_dev_test_for_anomaly_detection
import logging
import pandas as pd
from logai.dataloader.data_loader import FileDataLoader
from logai.preprocess.hdfs_preprocessor import HDFSPreprocessor
from logai.information_extraction.log_parser import LogParser
from logai.preprocess.openset_partitioner import OpenSetPartitioner
from logai.analysis.nn_anomaly_detector import NNAnomalyDetector
from logai.information_extraction.log_vectorizer import LogVectorizer
from logai.utils import constants


config_path = "../../../examples/jupyter_notebook/nn_ad_benchmarking/configs/hdfs_logbert_config.yaml"
config_parsed = read_file(config_path)
config_dict = config_parsed["workflow_config"]
config = OpenSetADWorkflowConfig.from_dict(config_dict)

loaded_filepath = os.path.join(config.output_dir, 'HDFS_1.5G_loaded.csv')
dataloader = FileDataLoader(config.data_loader_config)
logrecord = dataloader.load_data()
logrecord.save_to_csv(loaded_filepath)
print (logrecord.body[constants.LOGLINE_NAME])

preprocessor = HDFSPreprocessor(config.preprocessor_config, config.label_filepath)
preprocessed_filepath = os.path.join(config.output_dir, 'HDFS_1.5G_processed.csv')
logrecord = preprocessor.clean_log(logrecord)
logrecord.save_to_csv(preprocessed_filepath)
print (logrecord.body[constants.LOGLINE_NAME])

partitioner = OpenSetPartitioner(config.open_set_partitioner_config)
partitioned_filepath = os.path.join(config.output_dir, 'HDFS_1.5G_nonparsed_session.csv')
logrecord = partitioner.partition(logrecord)
logrecord.save_to_csv(partitioned_filepath)
print (logrecord.body[constants.LOGLINE_NAME])

train_filepath = os.path.join(config.output_dir, 'HDFS_1.5G_nonparsed_session_supervised_train.csv')
dev_filepath = os.path.join(config.output_dir, 'HDFS_1.5G_nonparsed_session_supervised_dev.csv')
test_filepath = os.path.join(config.output_dir, 'HDFS_1.5G_nonparsed_session_supervised_test.csv')

(train_data, dev_data, test_data) = split_train_dev_test_for_anomaly_detection(
                logrecord,training_type=config.training_type,
                test_data_frac_neg_class=config.test_data_frac_neg,
                test_data_frac_pos_class=config.test_data_frac_pos,
                shuffle=config.train_test_shuffle
            )

train_data.save_to_csv(train_filepath)
dev_data.save_to_csv(dev_filepath)
test_data.save_to_csv(test_filepath)
print ('Train/Dev/Test Anomalous', len(train_data.labels[train_data.labels[constants.LABELS]==1]),
                                   len(dev_data.labels[dev_data.labels[constants.LABELS]==1]),
                                   len(test_data.labels[test_data.labels[constants.LABELS]==1]))
print ('Train/Dev/Test Normal', len(train_data.labels[train_data.labels[constants.LABELS]==0]),
                                   len(dev_data.labels[dev_data.labels[constants.LABELS]==0]),
                                   len(test_data.labels[test_data.labels[constants.LABELS]==0]))



vectorizer = LogVectorizer(config.log_vectorizer_config)
vectorizer.fit(train_data)
train_features = vectorizer.transform(train_data)
dev_features = vectorizer.transform(dev_data)
test_features = vectorizer.transform(test_data)
print (train_features)


anomaly_detector = NNAnomalyDetector(config=config.nn_anomaly_detection_config)
anomaly_detector.fit(train_features, dev_features)

predict_results = anomaly_detector.predict(test_features)
print (predict_results)

# anomalies = predict_results["anom_score"]
#
# _ad_results = pd.DataFrame(anomalies.rename("result"))
#
# anomaly_group_indices = _ad_results[_ad_results["result"] > 0.0].index.values
#
# anomaly_indices = []
#
# for indices in anomaly_group_indices:
#     anomaly_indices += test_data.indices[indices]
#
# anomaly_labels = [True if i in anomaly_indices else False for i in test_data.indices]
#
# test_data.df['Is_Anomaly'] = anomaly_labels
#
# print(test_data)
# for indices in self._index_group["event_index"].iloc[anomaly_group_indices]:
#   anomaly_indices += indices
#
# df = pd.DataFrame(self.loglines)
# df["_id"] = df.index.values
#
# df["is_anomaly"] = [True if i in anomaly_indices else False for i in df["_id"]]
# self._loglines_with_anomalies = df
#
# res = (
#   self._loglines_with_anomalies.join(self.attributes)
#   .join(self.timestamps)
#   .join(self.event_group)
# )
# return res
