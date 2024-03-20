/*
https://zhuanlan.zhihu.com/p/76734219
先用前k个元素生成一个小顶堆，这个小顶堆用于存储，当前最大的k个元素
接着，从第k+1个元素开始扫描，和堆顶（堆中最小的元素）比较
如果被扫描的元素大于堆顶，则替换堆顶的元素，并调整堆
以保证堆内的k个元素，总是当前最大的k个元素
*/

function topK(arr, k) {
    // 构造堆并生成小顶堆
    const subArr = arr.slice(0, k)
    const restArr = arr.slice(k)

    let start = (subArr.length - 1) / 2
    for (let i = start; i >= 0; i--) {
        _minHeap(subArr, subArr.length, i)
    }

    // 此时 subArr 的 0 是最大的元素
    // 从 restArr 弹出一个元素与最大的元素比较
    while (restArr.length > 0) {
        let popNum = restArr.shift()
        if (popNum > subArr[0]) {
            subArr[0] = popNum
        }
    
        for (let i = start; i >= 0; i--) {
            _minHeap(subArr, subArr.length, i)
        }    
    }

    return subArr
}

function _minHeap(arr, size, index) {
    //左子节点
    let leftNode = 2 * index + 1
    //右子节点
    let rightNode = 2 * index + 2
    //先设当前为最大节点
    let max = index
    //和两个子节点分别对比，找出最大的节点
    if (leftNode < size && arr[leftNode] < arr[max]) {
        max = leftNode;
    }
    if (rightNode < size && arr[rightNode] < arr[max]) {
        max = rightNode;
    }

    //交换位置
    if (max != index) {
        let temp = arr[index]
        arr[index] = arr[max]
        arr[max] = temp
        //交换位置后，可能会破坏之前排好的堆，所以之间排好的堆需要重新调整
        _minHeap(arr, size, max)
    }
}

function __main() {
    // 复杂度是 O(n*lg(k))
    // k越小, 这个算法越有优势
    const array = [4, 6, 8, 5, 9, 10, 2, 1, 8, 2, 4, 7]
    const ret = topK(array, 3)
    console.log(ret)
}

__main()