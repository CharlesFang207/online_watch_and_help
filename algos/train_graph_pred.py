import torch
import time
import os
import glob
import yaml
import pickle as pkl
from tqdm import tqdm
import ipdb
from dataloader.dataloader_v2 import AgentTypeDataset
from dataloader import dataloader_v2 as dataloader_v2
from arguments import *
from torch import nn
import torch.optim as optim
from models import agent_pref_policy
from hydra.utils import get_original_cwd, to_absolute_path

import utils.utils_models as utils_models
from utils.utils_models import AverageMeter, ProgressMeter, LoggerSteps

import hydra
from omegaconf import DictConfig, OmegaConf
import pathlib


def merge2d(tensor):
    dim = list(tensor.shape)
    return tensor.reshape([-1]+dim[2:])

def unmerge(tensor, firstdim):
    dim = list(tensor.shape)
    return tensor.reshape([firstdim, -1] + dim[1:])

def evaluate(data_loader, data_loader_train, model, epoch, args, criterion, logger):
    model.eval()

    batch_time = AverageMeter('Time', ':6.3f')
    data_time = AverageMeter('Data', ':6.3f')
    losses = AverageMeter('Loss', ':.4e')
    losses_action = AverageMeter('LossAction', ':.4e')
    losses_o1 = AverageMeter('LossO1', ':.4e')
    losses_o2 = AverageMeter('LossO2', ':.4e')
    losses_goal = AverageMeter('LossGoal', ':.4e')
    losses_close = AverageMeter('LossClose', ':.4e')

    ### Performance metrics
    acc_action = AverageMeter('AccAction', ':6.2f')
    acc_o1 = AverageMeter('Acc O1', ':6.2f')
    acc_o2 = AverageMeter('Acc O2', ':6.2f')
    acc_goal = AverageMeter('Acc Goal', ':6.2f')
    acc_close = AverageMeter('Acc Close', ':6.2f')
    rec_goal = AverageMeter('Acc Goal', ':6.2f')
    rec_close = AverageMeter('Acc Close', ':6.2f')



    ## Performance per agent
    meter_dict = {}
    for i in range(15):
        meter_dict[i] = {}
        meter_dict[i]['count'] = 0
        meter_dict[i]['acc_action'] = AverageMeter('AccAction', ':6.2f')
        meter_dict[i]['acc_o1'] = AverageMeter('Acc O1', ':6.2f')
        meter_dict[i]['acc_o2'] = AverageMeter('Acc O2', ':6.2f')
        meter_dict[i]['acc_goal'] = AverageMeter('Acc Goal', ':6.2f')
        meter_dict[i]['acc_close'] = AverageMeter('Acc Close', ':6.2f')
        meter_dict[i]['rec_goal'] = AverageMeter('Acc Goal', ':6.2f')
        meter_dict[i]['rec_close'] = AverageMeter('Acc Close', ':6.2f')        


    progress = ProgressMeter(
            len(data_loader),
            [batch_time, data_time, losses, losses_action, losses_o1, losses_o2, acc_action, acc_o1, acc_o2],
        prefix="Epoch: [{}]".format(epoch))
    
    end = time.time()
    for it, data_item in enumerate(data_loader):
        if it < args['test']['num_iters']:
            data_time.update(time.time() - end)


            graph_info, program, label, len_mask, goal, label_agent, real_label_agent = data_item
            # ipdb.set_trace()
            inputs = {
                'program': program,
                'graph': graph_info,
                'mask_len': len_mask,
                'goal': goal,
                'label_agent': label_agent

            }
            ipdb.set_trace()
            with torch.no_grad():
                output = model(inputs)
            action_l, o1_l, o2_l = output['action_logits'], output['o1_logits'], output['o2_logits']
            pred_goal, pred_close = output['pred_goal'], output['pred_close']

            bs = action_l.shape[0]

            index_label_obj1 = program['indobj1'][:, 1:]
            index_label_obj2 = program['indobj2'][:, 1:]

            if index_label_obj2.max() > args['model']['max_nodes'] or index_label_obj1.max() > args['model']['max_nodes']:
                print("Error with indices", index_label_obj1.max().item(), index_label_obj2.max().item())
            label_action = program['action'][:, 1:]

            if args['cuda']:
                label_action = label_action.cuda()
                index_label_obj2 = index_label_obj2.cuda()
                index_label_obj1 = index_label_obj1.cuda()
                len_mask = len_mask.cuda()
                graph_info['mask_goal'] = graph_info['mask_goal'].cuda()
                graph_info['mask_close'] = graph_info['mask_close'].cuda()
                graph_info['mask_object'] = graph_info['mask_object'].cuda()

            # ipdb.set_trace()
            # ipdb.set_trace()
            loss_action = unmerge(criterion(merge2d(action_l), merge2d(label_action)), bs)
            loss_object1 = unmerge(criterion(merge2d(o1_l), merge2d(index_label_obj1)), bs)
            loss_object2 = unmerge(criterion(merge2d(o2_l), merge2d(index_label_obj2)), bs)

            len_mask_avg = len_mask/len_mask.sum(1)[:, None]

            loss_action = (loss_action * len_mask_avg).sum(1).mean(0)
            loss_object1 = (loss_object1 * len_mask_avg).sum(1).mean(0)
            loss_object2 = (loss_object2 * len_mask_avg).sum(1).mean(0)

            # idpb.set_trace()
            loss_goal = torch.nn.BCEWithLogitsLoss(reduction='none')(pred_goal, graph_info['mask_goal'])
            loss_close = torch.nn.BCEWithLogitsLoss(reduction='none')(pred_close, graph_info['mask_close'])
        
            # Average over nodes, over batch and over time
            mask_node_avg = graph_info['mask_object'] / (1e-9 + graph_info['mask_object'].sum(-1)[:, :, None])
            loss_goal = args['train']['loss_goal'] * ((loss_goal * mask_node_avg).sum(-1) * len_mask_avg).sum(1).mean(0)
            loss_close = args['train']['loss_close'] * ((loss_close * mask_node_avg).sum(-1) * len_mask_avg).sum(1).mean(0)


            loss = loss_action + loss_object1 + loss_object2 + loss_goal + loss_close

            # Update losses
            losses.update(loss.item())
            losses_action.update(loss_action.item())
            losses_o1.update(loss_object1.item())
            losses_o2.update(loss_object2.item())
            losses_goal.update(loss_goal.item())
            losses_close.update(loss_close.item())

            # Update accuracy
            pred_action = action_l.argmax(-1)
            pred_o1 = o1_l.argmax(-1)
            pred_o2 = o2_l.argmax(-1)

            action_accuracy = ((pred_action == label_action) * len_mask_avg).sum(1).mean(0)
            o1_accuracy = ((pred_o1 == index_label_obj1) * len_mask_avg).sum(1).mean(0)
            o2_accuracy = ((pred_o2 == index_label_obj2) * len_mask_avg).sum(1).mean(0)
            goal_accuracy = ((((pred_goal > 0.5) == graph_info['mask_goal']) * mask_node_avg).sum(-1) * len_mask_avg).sum(1).mean(0)
            close_accuracy = ((((pred_close > 0.5) == graph_info['mask_close']) * mask_node_avg).sum(-1) * len_mask_avg).sum(1).mean(0)
            
            pos_goal_avg = graph_info['mask_goal'] / ((graph_info['mask_goal'] == 1).sum(-1)[:, :, None] + 1e-9)
            pos_close_avg = graph_info['mask_close'] / ((graph_info['mask_close'] == 1).sum(-1)[:, :, None] + 1e-9)
            goal_recall = ((((pred_goal > 0.5) == graph_info['mask_goal']) * pos_goal_avg).sum(-1) * len_mask_avg).sum(1).mean(0)
            close_recall = ((((pred_close > 0.5) == graph_info['mask_close']) * pos_close_avg).sum(-1) * len_mask_avg).sum(1).mean(0)

            acc_action.update(action_accuracy.item())
            acc_o1.update(o1_accuracy.item())
            acc_o2.update(o2_accuracy.item())
            acc_goal.update(goal_accuracy.item())
            acc_close.update(close_accuracy.item())
            rec_goal.update(goal_recall.item())
            rec_close.update(close_recall.item())


            # Per agent stats
            action_accuracy = ((pred_action == label_action) * len_mask_avg).sum(1)
            o1_accuracy = ((pred_o1 == index_label_obj1) * len_mask_avg).sum(1)
            o2_accuracy = ((pred_o2 == index_label_obj2) * len_mask_avg).sum(1)

            goal_accuracy = ((((pred_goal > 0.5) == graph_info['mask_goal']) * mask_node_avg).sum(-1) * len_mask_avg).sum(1)
            close_accuracy = ((((pred_close > 0.5) == graph_info['mask_close']) * mask_node_avg).sum(-1) * len_mask_avg).sum(1)
            
            pos_goal_avg = graph_info['mask_goal'] / ((graph_info['mask_goal'] == 1).sum(-1)[:, :, None] + 1e-9)
            pos_close_avg = graph_info['mask_close'] / ((graph_info['mask_close'] == 1).sum(-1)[:, :, None] + 1e-9)
            goal_recall = ((((pred_goal > 0.5) == graph_info['mask_goal']) * pos_goal_avg).sum(-1) * len_mask_avg).sum(1)
            close_recall = ((((pred_close > 0.5) == graph_info['mask_close']) * pos_close_avg).sum(-1) * len_mask_avg).sum(1)


            for agent_id in meter_dict.keys():
                count_agent_id = (real_label_agent == agent_id).sum().item()
                if count_agent_id > 0:
                    meter_dict[agent_id]['count'] = count_agent_id

                    index_label_agent_id  = (real_label_agent == agent_id)


                    meter_dict[agent_id]['acc_action'].update(action_accuracy[index_label_agent_id].mean(0).item())
                    meter_dict[agent_id]['acc_o1'].update(o1_accuracy[index_label_agent_id].mean(0).item())
                    meter_dict[agent_id]['acc_o2'].update(o2_accuracy[index_label_agent_id].mean(0).item())
                    meter_dict[agent_id]['acc_goal'].update(goal_accuracy[index_label_agent_id].mean(0).item())
                    meter_dict[agent_id]['acc_close'].update(close_accuracy[index_label_agent_id].mean(0).item())
                    meter_dict[agent_id]['rec_goal'].update(goal_recall[index_label_agent_id].mean(0).item())
                    meter_dict[agent_id]['rec_close'].update(close_recall[index_label_agent_id].mean(0).item())
            
            # ipdb.set_trace()
            batch_time.update(time.time() - end)
            end = time.time()


        else:
            continue

        progress.display(it)
        

        
        # Print the prediction
        prog_gt = {'action': label_action, 'o1': index_label_obj1, 'o2': index_label_obj2, 'graph': graph_info, 'mask_len': len_mask}
        prog_pred = {'action': pred_action, 'o1': pred_o1, 'o2': pred_o2, 'graph': graph_info, 'mask_len': len_mask}

        str_results = utils_models.get_pred_results_str(data_loader.dataset.graph_helper, prog_gt, prog_pred)
        
        info_res = {
            'str': progress.display(it, do_print=False)+'\n'+str_results
        }
        logger.log_info(info_res)

    info_log = {
        'losses': {'total_val': losses.avg, 'action_val': losses_action.avg, 'object1_val': losses_o1.avg, 'object2_val': losses_o2.avg},
        'accuracy': {'action_val': acc_action.avg, 'object1_val': acc_o1.avg, 'object2_val': acc_o2.avg,  'goal_val':  acc_goal.avg, 'close_val': acc_close.avg, 'goal_recall_val': rec_goal.avg, 'close_recall_val': rec_close.avg}
        # 'misc': {'epoch': }
    }
    logger.log_data(len(data_loader_train) * epoch, info_log)

    info_log2 = {}
    for agent_id in meter_dict.keys():
        
        if meter_dict[agent_id]['count'] > 0:
            info_log2[agent_id] = {
                'accuracy': {
                    'action_val': meter_dict[agent_id]['acc_action'].val, 
                    'object1_val': meter_dict[agent_id]['acc_o1'].val, 
                    'object2_val': meter_dict[agent_id]['acc_o2'].val,  
                    'goal_val':  meter_dict[agent_id]['acc_goal'].val, 
                    'close_val': meter_dict[agent_id]['acc_close'].val, 
                    'goal_recall_val': meter_dict[agent_id]['rec_goal'].val, 
                    'close_recall_val': meter_dict[agent_id]['rec_close'].val 
                },
            }

    logger.log_data2(it + len(data_loader) * epoch, info_log2)


def train_epoch(data_loader, model, epoch, args, criterion, optimizer, logger):

    batch_time = AverageMeter('Time', ':6.3f')
    data_time = AverageMeter('Data', ':6.3f')
    losses = AverageMeter('Loss', ':.4e')
    losses_state = AverageMeter('LossState', ':.4e')
    losses_edge = AverageMeter('LossState', ':.4e')

    

    acc_state = AverageMeter('AccState', ':6.2f')
    acc_edge = AverageMeter('AccEdge', ':6.2f')
    
    progress = ProgressMeter(
            len(data_loader),
            [batch_time, data_time, losses, losses_state, losses_edge, acc_state, acc_edge],
        prefix="Epoch: [{}]".format(epoch))

    model.train()
    
    end = time.time()


    for it, data_item in enumerate(data_loader):
        data_time.update(time.time() - end)

        graph_info, program, label, len_mask, goal, label_agent, real_label_agent = data_item
        utils_models.print_graph(data_loader.dataset.graph_helper, graph_info, 0, 0)

        inputs = {
            'program': program,
            'graph': graph_info,
            'mask_len': len_mask,
            'goal': goal,
            'label_agent': label_agent
        }
        # print(inputs['graph']['graph'], inputs['graph']['mask_object'].sum())
        output = model(inputs)

        # loss states
        criterion_state = torch.nn.BCEWithLogitsLoss(reduction='none')
        loss_state = criterion_state(output['states'][:, 1:, ...], graph_info['states_objects'][:, :-1, ...].cuda()) 
        loss_state = loss_state *  graph_info['mask_object'][:, 1:, :, None].cuda()
        loss_state = loss_state.mean()

        # loss edges edges in prediction are stored as a B x Time x N x N x num_edge_class tensor
        # GT is stored as B x Time x Num_edges, we need to convert
        num_nodes = output['states'].shape[-2]
        gt_edges = torch.zeros_like(output['edges'])
        num_edges = gt_edges.shape[-1]
        edge_tuples = graph_info['edge_tuples']
        index_edges = edge_tuples[..., 0] * num_nodes + edge_tuples[..., 1]
        edge_types = graph_info['edge_classes'] - 1
        for it_edge in range(num_edges):
            index_edge = edge_types == it_edge
            index_edge_curr = index_edges[index_edge]
            gt_edges[..., index_edge_curr.long(), it_edge] = 1

        loss_edges = criterion_state(output['edges'], gt_edges.cuda()) 
        loss_edges = loss_edges * mask_edges.cuda()
        loss_edges = loss_edges.mean()


        loss = loss_edges + loss_state
        losses.update(loss.item())
        losses_state.update(loss_state.item())
        losses_edge.update(loss_edge.item())


        # Update accuracy
        # TODO: add accuracy metrics

        #goal_recall = ((((pred_goal > 0.5) == graph_info['mask_goal']) * pos_goal_avg).sum(-1) * len_mask_avg).sum(1)
        #close_recall = ((((pred_close > 0.5) == graph_info['mask_close']) * pos_close_avg).sum(-1) * len_mask_avg).sum(1)



        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        batch_time.update(time.time() - end)
        end = time.time()

        if it % args['log']['print_every'] == 0:
            progress.display(it)
        if it % args['log']['print_long_every'] == 0:
        
            info_log = {
                'losses': {'total': losses.val, 'state': losses_state.val, 'edge': losses_edge.val},
                'accuracy': {'state': acc_state.val, 'edge': acc_edge.val},
                'misc': {'epoch': epoch}
            }
            logger.log_data(it + len(data_loader) * epoch, info_log)
            
            # Print the prediction
            #logger.log_info(info_res)

    #logger.log_embeds(len(data_loader) * epoch, model.module.agent_embedding)
    print("Failed Elements...", data_loader.dataset.get_failures())


def get_loaders(args):
    print("Loading dataset...")
    print("Train: {}".format(args['data']['train_data']))
    print("Test: {}".format(args['data']['test_data']))
    curr_file = os.path.dirname(get_original_cwd())
    dataset = AgentTypeDataset(path_init='{}/agent_preferences/dataset/{}'.format(curr_file, args['data']['train_data']), args_config=args)
    dataset_test = AgentTypeDataset(path_init='{}/agent_preferences/dataset/{}'.format(curr_file, args['data']['test_data']), args_config=args)
    if args['model']['state_encoder'] == 'GNN':
        collate_fn = dataloader_v2.collate_fn
    else:
        collate_fn = None
    train_loader = torch.utils.data.DataLoader(
            dataset, batch_size=args['train']['batch_size'], 
            shuffle=True, num_workers=args['train']['num_workers'], pin_memory=True, collate_fn=collate_fn)

    test_loader = torch.utils.data.DataLoader(
            dataset_test, batch_size=args['train']['batch_size'], 
            shuffle=True, num_workers=args['train']['num_workers'], pin_memory=True, collate_fn=collate_fn)
    return train_loader, test_loader



@hydra.main(config_path="../config/agent_pred_graph", config_name="config_default")
def main(cfg: DictConfig):
    config = cfg
    print("Config")
    print(OmegaConf.to_yaml(cfg))
    # ipdb.set_trace()

    train_loader, test_loader = get_loaders(config)
    if config.model.gated:
        model = agent_pref_policy.GraphPredNetwork(config)
    else:
        model = agent_pref_policy.GraphPredNetwork(config)

    print("CUDA: {}".format(cfg.cuda))
    if cfg.cuda:
        model = model.cuda()
        model = nn.DataParallel(model)
    criterion = nn.CrossEntropyLoss(reduction='none')
    optimizer = optim.Adam(model.parameters(), lr=config['train']['lr'])
    print("Failures: ", train_loader.dataset.get_failures())

    logger = LoggerSteps(config)

    logger.save_model(0, model, optimizer)

    for epoch in range(config['train']['epochs']):
        train_epoch(train_loader, model, epoch, config, criterion, optimizer, logger)
        evaluate(test_loader, train_loader, model, epoch, config, criterion, logger)
        if epoch % 10 == 0:
            logger.save_model(epoch, model, optimizer)


if __name__ == '__main__':
      main()
