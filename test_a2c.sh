#CUDA_VISIBLE_DEVICES=0 python test_a2c.py \
#--num-per-apartment 3 \
#--max-num-edges 500 --max-episode-length 30 \
#--balanced_sample --neg_ratio 0.5 --batch_size 16 \
#--obs_type full --gamma 0.95 --lr 1e-5 \
#--base-port 8084 --task_type find  --task-set full \
#--logging --nb_episodes 100000 --save-interval 200
##--use-editor

#--logging
#CUDA_VISIBLE_DEVICES=0 python test_a2c.py \
#--num-per-apartment 3 \
#--max-num-edges 500 --max-episode-length 30 \
#--balanced_sample --neg_ratio 0.5 --batch_size 16 \
#--obs_type full --gamma 0.95 --lr 1e-5 \
#--base-port 8080 --task_type find  --task-set setup_table \
#--nb_episodes 100000 --save-interval 200 \
#--use-editor

#--logging


# Python
CUDA_VISIBLE_DEVICES=0 python test_a2c.py \
--num-per-apartment 3 \
--max-num-edges 200 --max-episode-length 30 \
--balanced_sample --neg_ratio 0.5 --batch_size 16 \
--obs_type full --gamma 0.95 --lr 1e-4 \
--task_type find  --task-set setup_table \
--nb_episodes 100000 --save-interval 200 --simulator-type unity \
--base_net TF --debug --logging --log-interval 1 \
--base-port 8181
